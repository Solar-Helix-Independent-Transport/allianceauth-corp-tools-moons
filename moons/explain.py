"""Step by step working of a scanned moon's value, tax and rent, for /moons explain.
Built on scans.moon_values and rent.rent_breakdown so it shows what /moons price uses."""
from decimal import Decimal

from eve_sde.models import ItemType, ItemTypeMaterials

from . import app_settings, rent, scans
from .helpers import OreHelper
from .models import OrePrice, OreTax

RULE = "=" * 60
RARITIES = ("ore_rate", "ubiquitous_rate", "common_rate", "uncommon_rate", "rare_rate", "exceptional_rate")
# stored OreTax is kept to 2 places
STALE_TOLERANCE = Decimal("0.01")


def _pct(value):
    return f"{float(value):g}%"


def _when(dt):
    return dt.strftime("%Y-%m-%d %H:%M") if dt else "never"


def explain_moon(v, tax_rate, fuel=None, rental=None):
    """Lines explaining MoonValue `v` under OreTaxRates `tax_rate`.
    `fuel` is a rent.MetenoxFuel (used only if the profile subtracts it), `rental` the active MoonRental."""
    lines = []
    add = lines.append
    m3_per_hour = tax_rate.drill_m3_per_hour or app_settings.drill_m3_per_hour()
    units_per_fraction = scans.HOURS_30D * m3_per_hour / scans.MOON_ORE_M3_PER_UNIT
    goo_only = tax_rate.ignore_ores_in_refine

    ore_ids = {line.ore_id for line in v.ore_lines}
    priced_ids = {line.priced_as for line in v.ore_lines}
    types = {
        type_id: (name, group_id, portion)
        for type_id, name, group_id, portion in ItemType.objects.filter(
            id__in=ore_ids | priced_ids).values_list("id", "name", "group_id", "portion_size")
    }
    minerals = {}
    for type_id, name, qty, group_id in ItemTypeMaterials.objects.filter(item_type_id__in=priced_ids).values_list(
            "item_type_id", "material_item_type__name", "quantity", "material_item_type__group_id"):
        if goo_only and group_id == OreHelper.minerals_group_id:
            continue
        minerals.setdefault(type_id, []).append(f"{qty:,} {name}")
    price_updated = dict(OrePrice.objects.filter(
        item_id__in=priced_ids, goo_only=goo_only).values_list("item_id", "last_update"))
    tax_updated = dict(OreTax.objects.filter(
        item_id__in=ore_ids, tax=tax_rate).values_list("item_id", "last_update"))

    add(f"Moon price explanation: {v.name}")
    add(f"{v.system} / {v.region}  R{v.rarity or '-'}")
    add(RULE)
    add(f"INPUTS - ore tax `{tax_rate.tag}` (OreTaxRates id {tax_rate.pk})")
    add(f"  refine_rate              {_pct(tax_rate.refine_rate)}")
    for rarity in RARITIES:
        add(f"  {rarity.ljust(25)}{_pct(getattr(tax_rate, rarity))}")
    add(f"  ignore_ores_in_refine    {goo_only}")
    add(f"  tax_on_base_ore_value    {tax_rate.tax_on_base_ore_value}")
    source = "profile" if tax_rate.drill_m3_per_hour else "MOONS_DRILL_M3_PER_HOUR"
    add(f"  drill rate               {m3_per_hour:,} m3/h ({source})")
    add(f"  30 days                  {scans.HOURS_30D} h")
    add(f"  units per 100%           {scans.HOURS_30D} h x {m3_per_hour:,} m3/h / {scans.MOON_ORE_M3_PER_UNIT} m3"
        f" = {units_per_fraction:,.0f}")
    add(f"  rent_subtract_metenox    {tax_rate.rent_subtract_metenox_fuel}")
    add(f"  rent_profit_share        {_pct(tax_rate.rent_profit_share)}")
    add(f"  rent_minimum             Ƶ{tax_rate.rent_minimum:,}")

    add("")
    add(RULE)
    add("STEP 1 - Value and tax per ore")
    add(f"  OrePrice = Jita value of what one unit refines into{' (moon materials only)' if goo_only else ''}")
    add("  Value    = OrePrice x refine_rate")
    add("  OreTax   = Value x rarity rate (stored per profile, refreshed with ore prices)")
    for line in v.ore_lines:
        name, group_id, _ = types.get(line.ore_id, (line.name, None, None))
        rarity = OreHelper.rank_ids.get(group_id, "ore_rate")
        rate = getattr(tax_rate, rarity)
        add("")
        add(f"  {line.name} ({line.ore_id}) - {rarity} {_pct(rate)}")
        add(f"    {line.fraction * 100:.2f}% x {units_per_fraction:,.0f} = {line.units:,.0f} units")
        if line.priced_as != line.ore_id:
            add(f"    Priced as base ore {types.get(line.priced_as, (line.priced_as,))[0]} ({line.priced_as})")
        if line.price is None:
            add(f"    !! No OrePrice{' (goo only)' if goo_only else ''} - valued and taxed at 0")
            continue
        _, _, portion = types.get(line.priced_as, (None, None, None))
        if minerals.get(line.priced_as):
            add(f"    Refines ({portion} units): {', '.join(minerals[line.priced_as])}")
        add(f"    OrePrice Ƶ{line.price:,.2f}/unit (updated {_when(price_updated.get(line.priced_as))})")
        add(f"    Value  = {line.price:,.2f} x {_pct(tax_rate.refine_rate)} = Ƶ{line.unit_value:,.2f}/unit")
        expected = line.unit_value * Decimal(rate) / 100
        add(f"    OreTax = {line.unit_value:,.2f} x {_pct(rate)} = Ƶ{expected:,.2f}/unit")
        add(f"    Stored OreTax used: Ƶ{line.unit_tax:,.2f}/unit (updated {_when(tax_updated.get(line.ore_id))})")
        if abs(line.unit_tax - expected) > STALE_TOLERANCE:
            add("    !! Stored OreTax differs from the recalculation (ore prices changed since?)")
        add(f"    30d value {line.units:,.0f} x {line.unit_value:,.2f} = Ƶ{line.units * line.unit_value:,.0f}")
        add(f"    30d tax   {line.units:,.0f} x {line.unit_tax:,.2f} = Ƶ{line.units * line.unit_tax:,.0f}")
    if v.total_fraction < Decimal("0.995"):
        add("")
        add(f"  Composition totals {v.total_fraction * 100:.1f}%, not scaled up")

    r = rent.rent_breakdown(v.tax_30d, tax_rate, fuel)
    add("")
    add(RULE)
    if r.fuel:
        f = r.fuel
        add("STEP 2 - 30d Metenox fuel")
        add(f"  Fuzzwork region {rent.FUEL_MARKET_REGION_ID}, {app_settings.fuel_buy_sell()} / {app_settings.fuel_bucket()}")
        add(f"  Magmatic Gas             Ƶ{f.gas_price:,.2f}")
        if f.gas_adjusted != f.gas_price:
            add(f"  Over Ƶ{rent.GAS_SOFT_CAP:,} so softened by gas factor {app_settings.fuel_gas_factor()}:")
            add(f"    {rent.GAS_SOFT_CAP:,} + ({f.gas_price:,.2f} - {rent.GAS_SOFT_CAP:,}) / {app_settings.fuel_gas_factor()}"
                f" = Ƶ{f.gas_adjusted:,.2f}")
        add(f"  Gas 30d = {f.gas_adjusted:,.2f} x {rent.HOURS_30D} h x {f.gas_per_hour}/h = Ƶ{f.gas_30d:,.0f}")
        for block, price in f.block_prices.items():
            add(f"  {block.ljust(25)}Ƶ{price:,.2f}")
        add(f"  Average block            Ƶ{f.block_average:,.2f}")
        add(f"  Blocks 30d = {f.block_average:,.2f} x {rent.HOURS_30D} h x {rent.BLOCKS_PER_HOUR}/h"
            f" = Ƶ{f.blocks_30d:,.0f}")
        add(f"  Fuel 30d = {f.gas_30d:,.0f} + {f.blocks_30d:,.0f} = Ƶ{f.total_30d:,.0f}")
    else:
        add("STEP 2 - 30d Metenox fuel")
        add("  Not subtracted by this profile")

    add("")
    add(RULE)
    add("STEP 3 - Moon value and rent")
    for line in v.ore_lines:
        add(f"  {line.name[:24].ljust(25)}value Ƶ{line.units * (line.unit_value or 0):,.0f}"
            f"  tax Ƶ{line.units * line.unit_tax:,.0f}")
    add(f"  Value 30d                Ƶ{v.value_30d:,.0f}")
    add(f"  Tax 30d                  Ƶ{r.tax_30d:,.0f}")
    if r.fuel:
        add(f"  Profit = {r.tax_30d:,.0f} - {r.fuel.total_30d:,.0f} fuel = Ƶ{r.profit:,.0f}")
    add(f"  Rent   = {r.profit:,.0f} x {_pct(r.share)} = Ƶ{r.raw:,.0f}")
    add(f"  Rounded to nearest 1m    Ƶ{r.rounded:,}")
    add(f"  Minimum Ƶ{r.minimum:,}".ljust(27) + f"Ƶ{r.final:,}")
    add(f"  Suggested rent           Ƶ{r.final:,}")
    if rental:
        add(f"  Current rent             Ƶ{rental.price:,} ({rental.contact.character_name}),"
            f" delta Ƶ{r.final - rental.price:,}")
    return lines
