import re
from dataclasses import dataclass, field
from decimal import Decimal

from eve_sde.models import ItemType, Moon, TypeDogma

from django.db import transaction
from django.utils import timezone

from . import app_settings
from .helpers import OreHelper
from .models import MoonScan, MoonScanOre, OrePrice, OreTax

# non-English clients wrap names as <localized hint="English">Local</localized>
LOCALIZED = re.compile(r'<localized hint="([^"]*)">[^<]*</localized>')

NEW = "new"
UNCHANGED = "unchanged"
CHANGED = "changed"
NEEDS_CHANGE_PERM = "needs_change_perm"
REJECTED = "rejected"

HOURS_30D = 720
MOON_ORE_M3_PER_UNIT = 10

# re-scans of the same moon agree to this precision
SAME_SCAN_PLACES = Decimal("0.0001")


@dataclass
class ParsedMoon:
    moon_id: int
    name: str
    ores: dict = field(default_factory=dict)  # ore id -> fraction, as pasted


def _ore_line(fields):
    """Ore lines start with an empty field and carry
    name, quantity, type id, system id, planet id, moon id."""
    if len(fields) < 7 or fields[0].strip():
        return None
    try:
        return (
            Decimal(fields[2].strip()),
            int(fields[3]),
            int(fields[6]),
        )
    except (ArithmeticError, ValueError):
        return None


def parse_moon_scan(text):
    moons = {}
    heading = ""
    text = LOCALIZED.sub(r"\1", text)
    # pastes relayed through Discord/forums arrive with tabs as 4 spaces
    for line in text.replace("    ", "\t").splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        ore = _ore_line(fields)
        if ore:
            fraction, type_id, moon_id = ore
            moon = moons.setdefault(moon_id, ParsedMoon(moon_id, heading))
            moon.ores[type_id] = fraction
        elif len(fields) < 7:
            # moon heading; the header row has 7 columns and is skipped
            heading = fields[0].strip()
    return list(moons.values())


@dataclass
class MoonImportResult:
    moon_id: int
    name: str
    status: str
    reason: str = ""
    flagged: list = field(default_factory=list)
    ores: dict = field(default_factory=dict)  # ore id -> pasted fraction
    previous: dict = field(default_factory=dict)  # ore id -> stored fraction
    ore_names: dict = field(default_factory=dict)


def _rounded(ores):
    return {type_id: Decimal(fraction).quantize(SAME_SCAN_PLACES) for type_id, fraction in ores.items()}


def _plan(text, user):
    can_change = user.has_perm("moons.change_moonscan")
    parsed_moons = parse_moon_scan(text)
    moon_ids = [p.moon_id for p in parsed_moons]
    moons = Moon.objects.in_bulk(moon_ids)
    types = ItemType.objects.in_bulk({t for p in parsed_moons for t in p.ores})
    stored_scans = MoonScan.objects.filter(moon_id__in=moon_ids).prefetch_related("ores__ore")
    existing = {}
    ore_names = {t.id: t.name for t in types.values()}
    for scan in stored_scans:
        existing[scan.moon_id] = {o.ore_id: o.fraction for o in scan.ores.all()}
        ore_names.update({o.ore_id: o.ore.name for o in scan.ores.all()})

    plan = []
    for parsed in parsed_moons:
        moon = moons.get(parsed.moon_id)
        if not moon:
            result = MoonImportResult(parsed.moon_id, parsed.name, REJECTED, "Unknown moon ID")
        elif unknown := sorted(t for t in parsed.ores if t not in types):
            result = MoonImportResult(
                moon.id, moon.name, REJECTED,
                f"Unknown ore type {', '.join(str(t) for t in unknown)}")
        elif moon.id not in existing:
            result = MoonImportResult(moon.id, moon.name, NEW)
        elif _rounded(existing[moon.id]) == _rounded(parsed.ores):
            result = MoonImportResult(moon.id, moon.name, UNCHANGED)
        else:
            result = MoonImportResult(moon.id, moon.name, CHANGED if can_change else NEEDS_CHANGE_PERM)
        result.ores = parsed.ores
        result.previous = existing.get(parsed.moon_id, {})
        result.ore_names = {t: ore_names[t] for t in {*result.ores, *result.previous} if t in ore_names}
        if result.status != REJECTED:
            # old scans can list ores CCP has since moved off moons; keep them, but say so
            result.flagged = [
                types[t].name for t in parsed.ores if types[t].group_id not in OreHelper.rank_ids
            ]
        plan.append((parsed, result))
    return plan


def preview_import(text, user):
    """What an import would do, per moon. Writes nothing."""
    return [result for _, result in _plan(text, user)]


@transaction.atomic
def commit_import(text, user):
    plan = _plan(text, user)
    now = timezone.now()
    for parsed, result in plan:
        if result.status not in (NEW, CHANGED):
            continue
        MoonScan.objects.filter(moon_id=parsed.moon_id).delete()
        scan = MoonScan.objects.create(moon_id=parsed.moon_id, added_by=user, added_at=now)
        MoonScanOre.objects.bulk_create(
            MoonScanOre(scan=scan, ore_id=type_id, fraction=fraction)
            for type_id, fraction in parsed.ores.items()
        )
    return [result for _, result in plan]


@dataclass
class MoonValue:
    moon_id: int
    name: str
    value_30d: Decimal
    tax_30d: Decimal
    total_fraction: Decimal
    unpriced: list
    added_at: object
    added_by: object
    system: str = ""
    region: str = ""
    ores: list = field(default_factory=list)  # (ore id, name, fraction)


def moon_values(tax_rate, moon_ids=None):
    """Each scanned moon's 30 day value and tax under one OreTaxRates profile.
    Fractions are used as stored, never scaled up to 100%."""
    units_per_fraction = Decimal(
        HOURS_30D * app_settings.drill_m3_per_hour() / MOON_ORE_M3_PER_UNIT)
    refine = Decimal(tax_rate.refine_rate) / 100
    prices = dict(
        OrePrice.objects.filter(goo_only=tax_rate.ignore_ores_in_refine)
        .values_list("item_id", "price"))
    taxes = dict(OreTax.objects.filter(tax=tax_rate).values_list("item_id", "price"))
    base_ore = {}
    if tax_rate.tax_on_base_ore_value:
        base_ore = {
            type_id: int(base_id) for type_id, base_id in TypeDogma.objects.filter(
                dogma_attribute_id=OreHelper.base_ore_dogma_attribute_id,
                item_type_id__in=MoonScanOre.objects.values("ore_id"),
            ).values_list("item_type_id", "value")
        }

    values = []
    scans = MoonScan.objects.select_related(
        "moon__solar_system__constellation__region", "added_by__profile__main_character",
    ).prefetch_related("ores__ore")
    if moon_ids is not None:
        scans = scans.filter(moon_id__in=moon_ids)
    for scan in scans:
        value = tax = total = Decimal(0)
        unpriced = []
        for o in scan.ores.all():
            units = o.fraction * units_per_fraction
            total += o.fraction
            priced_as = base_ore.get(o.ore_id, o.ore_id)
            if priced_as not in prices:
                unpriced.append(o.ore.name)
                continue
            value += units * prices[priced_as] * refine
            tax += units * taxes.get(o.ore_id, 0)
        system = scan.moon.solar_system
        values.append(MoonValue(
            scan.moon_id, scan.moon.name, value, tax, total, unpriced, scan.added_at, scan.added_by,
            system=system.name, region=system.constellation.region.name,
            ores=[(o.ore_id, o.ore.name, o.fraction) for o in scan.ores.all()],
        ))
    return values
