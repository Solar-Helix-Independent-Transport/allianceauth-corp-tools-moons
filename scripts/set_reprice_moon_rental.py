"""
One-off: set the reprice method of every active rental to the "Moon Rental" ore tax,
except rentals by the "Initiative Trust" corporation, which are left as they are.

Not shipped with the package. Run it from the auth project:

    python manage.py shell < /path/to/set_reprice_moon_rental.py

Set DRY_RUN=1 in the environment to only print what would be changed.
"""
import os

from moons.models import MoonRental, OreTaxRates

REPRICE_TAG = "Moon Rental"
EXCLUDED_CORP = "Initiative Trust"

DRY_RUN = os.environ.get("DRY_RUN") == "1"

method = OreTaxRates.objects.get(tag=REPRICE_TAG)

rentals = MoonRental.objects.filter(end_date__isnull=True).exclude(
    corporation__corporation_name=EXCLUDED_CORP
).exclude(reprice_method=method).select_related("moon", "corporation", "reprice_method")

for r in rentals:
    old = r.reprice_method.tag if r.reprice_method else "None"
    print(f"{r.moon.name} ({r.corporation.corporation_name}): {old} -> {method.tag}")

print(f"{rentals.count()} rentals to update")

if DRY_RUN:
    print("DRY_RUN set, nothing changed")
else:
    updated = rentals.update(reprice_method=method)
    print(f"Updated {updated} rentals")
