"""
Preview a full reprice_rentals run without changing anything or messaging anyone.

Not shipped with the package. Run it from the auth project:

    python manage.py shell < /path/to/preview_reprice.py

Set WITH_MOON_RENTAL=1 to preview as if set_reprice_moon_rental.py had been run first:
every active rental not by "Initiative Trust" gets the "Moon Rental" reprice method,
inside a transaction that is rolled back afterwards.
"""
import os
from types import SimpleNamespace

from django.db import transaction

from moons import repricing as rp
from moons.models import MoonRental, OreTaxRates

REPRICE_TAG = "Moon Rental"
EXCLUDED_CORP = "Initiative Trust"

WITH_MOON_RENTAL = os.environ.get("WITH_MOON_RENTAL") == "1"


class Rollback(Exception):
    pass


try:
    with transaction.atomic():
        if WITH_MOON_RENTAL:
            method = OreTaxRates.objects.get(tag=REPRICE_TAG)
            n = MoonRental.objects.filter(end_date__isnull=True).exclude(
                corporation__corporation_name=EXCLUDED_CORP
            ).update(reprice_method=method)
            print(f"(Previewing with {n} rentals set to {REPRICE_TAG}, rolled back after)\n")

        result = rp.reprice(SimpleNamespace(dry_run=True))

        print("\n".join(rp.summary_lines(result)))
        print()
        print(f"{'Moon'.ljust(30)}{'Old Price'.ljust(20)}{'New Price'.ljust(20)}{'Delta'.ljust(20)}Method")
        print(rp.RULE)
        for c in result.changes:
            print(rp._row(c.rental.moon.name, c.old, c.new) + c.rental.reprice_method.tag)
        raise Rollback
except Rollback:
    pass
