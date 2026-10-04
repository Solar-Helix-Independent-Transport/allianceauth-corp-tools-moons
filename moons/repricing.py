"""Reprice active rentals to their suggested rent, for the reprice_rentals task.
Ported from corp-tools-compliance's price_moons, on the scan valuation."""
from dataclasses import dataclass, field

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from . import rent, scans
from .models import MoonRental

RULE = "-" * 90


@dataclass
class RentalChange:
    rental: MoonRental
    owner_pk: int
    old: int
    new: int


@dataclass
class RepricingResult:
    title: str
    fuel: dict = field(default_factory=dict)  # ore tax tag -> rent.MetenoxFuel, when it subtracts fuel
    changes: list = field(default_factory=list)
    skipped: list = field(default_factory=list)  # "moon (why)"

    @property
    def total_old(self):
        return sum(c.old for c in self.changes)

    @property
    def total_new(self):
        return sum(c.new for c in self.changes)


def _owner_pk(character):
    try:
        return character.character_ownership.user_id
    except ObjectDoesNotExist:
        return None


def reprice(settings):
    """Work out, and unless it's a dry run save, the new price of every active rental
    with a reprice method. Raises rent.FuelPricesUnavailable rather than price without
    fuel when a reprice method subtracts it."""
    rentals = list(MoonRental.objects.filter(
        end_date__isnull=True, price__gte=1, reprice_method__isnull=False,
    ).select_related(
        "moon", "contact", "contact__character_ownership", "reprice_method",
    ).order_by("moon__name"))

    result = RepricingResult(
        "Projected Metenox Rental Prices" if settings.dry_run else "Updated Metenox Rental Prices")
    by_method = {}
    for rental in rentals:
        by_method.setdefault(rental.reprice_method_id, []).append(rental)
    new_prices, unpriced = {}, {}
    for group in by_method.values():
        tax_rate = group[0].reprice_method
        fuel = rent.fuel_for(tax_rate)
        if fuel:
            result.fuel[tax_rate.tag] = fuel
        values = {v.moon_id: v for v in scans.moon_values(tax_rate, moon_ids=[r.moon_id for r in group])}
        for rental in group:
            v = values.get(rental.moon_id)
            if v and v.tax_30d:
                new_prices[rental.pk] = rent.rent_breakdown(v.tax_30d, tax_rate, fuel).final
            else:
                unpriced[rental.pk] = "No Moon Scan" if not v else "No Value"

    today = timezone.now().strftime("%Y/%m/%d")
    for rental in rentals:
        owner = _owner_pk(rental.contact)
        if owner is None:
            result.skipped.append(f"{rental.moon.name} (Unknown Owner: {rental.contact.character_name})")
        elif rental.pk in unpriced:
            result.skipped.append(f"{rental.moon.name} ({rental.contact.character_name}) ({unpriced[rental.pk]})")
        else:
            new = new_prices[rental.pk]
            result.changes.append(RentalChange(rental, owner, rental.price, new))
            if not settings.dry_run:
                rental.note += f"\n{today} - Old: {rental.price:,} - New: {new:,}"
                rental.price = new
                rental.save(update_fields=["note", "price"])
    return result


def _fuel_line(result):
    # every reprice method that subtracts fuel uses the same (cached) prices
    f = next(iter(result.fuel.values()), None)
    if not f:
        return "Metenox fuel not subtracted"
    return f"Gas: Ƶ{f.gas_adjusted:,.0f}\nBlocks: Ƶ{f.block_average:,.0f}\n30d Fuel: Ƶ{f.total_30d:,.0f}"


def _row(name, old, new):
    return f"{name[:29].ljust(30)}{f'Ƶ{old:,}'.ljust(20)}{f'Ƶ{new:,}'.ljust(20)}{f'Ƶ{new - old:,}'.ljust(20)}"


def renter_lines(result):
    """{user pk: lines} telling each renter their moons' new prices."""
    by_owner = {}
    for c in result.changes:
        by_owner.setdefault(c.owner_pk, []).append(c)
    messages = {}
    for owner, changes in by_owner.items():
        lines = [f"{result.title}\n", _fuel_line(result), RULE,
                 f"{'Moon'.ljust(30)}{'Old Price'.ljust(20)}{'New Price'.ljust(20)}{'Delta'.ljust(20)}", RULE]
        lines += [_row(c.rental.moon.name, c.old, c.new) for c in changes]
        lines += [RULE, f"{'Total: '.ljust(50)}Ƶ{sum(c.new for c in changes):,}"]
        messages[owner] = lines
    return messages


def summary_lines(result):
    methods = {}
    for c in result.changes:
        methods[c.rental.reprice_method.tag] = methods.get(c.rental.reprice_method.tag, 0) + 1
    lines = [
        f"{result.title}\n",
        f"Reprice methods: {', '.join(f'{tag} ({n:,})' for tag, n in sorted(methods.items())) or 'none'}",
        _fuel_line(result),
        f"Total moons updated: {len(result.changes):,}",
        f"Bad moons:           {len(result.skipped):,}",
        f"Total Renters:       {len({c.owner_pk for c in result.changes}):,}",
    ]
    lines += [f"           - {s}" for s in result.skipped]
    lines += [
        f"Total old Tax:       Ƶ{result.total_old:,}",
        f"Total new Tax:       Ƶ{result.total_new:,}",
        f"Total delta:         Ƶ{result.total_new - result.total_old:,}",
    ]
    return lines
