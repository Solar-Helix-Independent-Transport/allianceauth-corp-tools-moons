"""
Why active rentals come out "No Value" in reprice_rentals: groups them by cause.

Not shipped with the package. Run it from the auth project:

    python manage.py shell < /path/to/diagnose_no_value.py
"""
from collections import Counter

from moons import scans
from moons.models import MoonRental

rentals = MoonRental.objects.filter(
    end_date__isnull=True, price__gte=1, reprice_method__isnull=False,
).select_related("moon", "reprice_method")

by_method = {}
for r in rentals:
    by_method.setdefault(r.reprice_method, []).append(r)

for method, group in by_method.items():
    print(f"== {method.tag}: rates ore {method.ore_rate} ubiq {method.ubiquitous_rate} "
          f"common {method.common_rate} uncommon {method.uncommon_rate} rare {method.rare_rate} "
          f"exceptional {method.exceptional_rate}")
    values = {v.moon_id: v for v in scans.moon_values(method, moon_ids=[r.moon_id for r in group])}
    causes = Counter()
    unpriced_ores = Counter()
    zero_tax_ores = Counter()
    examples = {}
    for r in group:
        v = values.get(r.moon_id)
        if not v or v.tax_30d:
            continue
        if not v.ores:
            cause = "scan has no ores"
        elif len(v.unpriced) == len(v.ores):
            cause = "no ore prices for any ore"
            unpriced_ores.update(v.unpriced)
        else:
            cause = "ores priced but tax is 0"
            zero_tax_ores.update(line.name for line in v.ore_lines if line.unit_value is not None)
        causes[cause] += 1
        examples.setdefault(cause, r.moon.name)
    for cause, n in causes.most_common():
        print(f"{n:5}  {cause}  (e.g. {examples[cause]})")
    if unpriced_ores:
        print("  Unpriced ores:", ", ".join(f"{o} ({n})" for o, n in unpriced_ores.most_common()))
    if zero_tax_ores:
        print("  Ores on zero-tax moons:", ", ".join(f"{o} ({n})" for o, n in zero_tax_ores.most_common()))
