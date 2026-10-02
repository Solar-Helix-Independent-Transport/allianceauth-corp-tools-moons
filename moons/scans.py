import re
from dataclasses import dataclass, field
from decimal import Decimal

from eve_sde.models import ItemType, Moon

from django.db import transaction
from django.utils import timezone

from .helpers import OreHelper
from .models import MoonScan, MoonScanOre

# non-English clients wrap names as <localized hint="English">Local</localized>
LOCALIZED = re.compile(r'<localized hint="([^"]*)">[^<]*</localized>')

NEW = "new"
UNCHANGED = "unchanged"
CHANGED = "changed"
NEEDS_CHANGE_PERM = "needs_change_perm"
REJECTED = "rejected"

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


def _rounded(ores):
    return {type_id: Decimal(fraction).quantize(SAME_SCAN_PLACES) for type_id, fraction in ores.items()}


def _plan(text, user):
    can_change = user.has_perm("moons.change_moonscan")
    parsed_moons = parse_moon_scan(text)
    moon_ids = [p.moon_id for p in parsed_moons]
    moons = Moon.objects.in_bulk(moon_ids)
    types = ItemType.objects.in_bulk({t for p in parsed_moons for t in p.ores})
    existing = {
        scan.moon_id: {o.ore_id: o.fraction for o in scan.ores.all()}
        for scan in MoonScan.objects.filter(moon_id__in=moon_ids).prefetch_related("ores")
    }

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
