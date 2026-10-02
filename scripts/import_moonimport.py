"""
One-off bulk import of moon compositions from the private `moonimport` app
(allianceauth-moon-import) into moons.MoonScan / MoonScanOre.

Not shipped with the package. Run it from the auth project, with both apps installed:

    python manage.py shell < /path/to/import_moonimport.py

Set DRY_RUN=1 in the environment to only print what would be imported.

- Moons that already have a scan are skipped, so real in-game scans always win
  and re-running only fills new gaps.
- Moons or ore types missing from eve_sde are skipped and counted.
- Fractions are stored as given (moonimport `distribution` is already 0-1), never scaled.
- Imported scans have no `added_by`, which marks them as bulk imported.
"""
import os
from collections import Counter
from decimal import Decimal

from eve_sde.models import ItemType, Moon as SdeMoon
from moonimport.models import MoonOres

from django.db import transaction
from django.utils import timezone

from moons.models import MoonScan, MoonScanOre

BATCH = 1000


def run(dry_run=False):
    known_moons = set(SdeMoon.objects.values_list("id", flat=True))
    known_types = set(ItemType.objects.values_list("id", flat=True))
    scanned = set(MoonScan.objects.values_list("moon_id", flat=True))

    compositions = {}
    for moon_id, type_id, distribution in MoonOres.objects.values_list(
        "moon_id_id", "type_id", "distribution"
    ).iterator(chunk_size=10000):
        compositions.setdefault(moon_id, {})[type_id] = Decimal(str(distribution))

    skipped = Counter()
    to_import = {}
    for moon_id, ores in compositions.items():
        if moon_id in scanned:
            skipped["already scanned"] += 1
        elif moon_id not in known_moons:
            skipped["moon not in eve_sde"] += 1
        elif any(t not in known_types for t in ores):
            skipped["ore type not in eve_sde"] += 1
        else:
            to_import[moon_id] = ores

    print(f"moonimport moons with ores: {len(compositions)}")
    for reason, count in skipped.items():
        print(f"skipped, {reason}: {count}")
    print(f"{'would import' if dry_run else 'importing'}: {len(to_import)}")
    if dry_run:
        return

    now = timezone.now()
    moon_ids = list(to_import)
    for start in range(0, len(moon_ids), BATCH):
        batch = moon_ids[start:start + BATCH]
        with transaction.atomic():
            MoonScan.objects.bulk_create(
                [MoonScan(moon_id=m, added_by=None, added_at=now) for m in batch],
                ignore_conflicts=True,  # a scan pasted while this runs wins
            )
            # re-read ids: not every database returns pks from bulk_create
            scan_ids = dict(
                MoonScan.objects.filter(moon_id__in=batch, added_by__isnull=True, added_at=now)
                .values_list("moon_id", "id")
            )
            MoonScanOre.objects.bulk_create(
                MoonScanOre(scan_id=scan_ids[m], ore_id=t, fraction=f)
                for m in batch if m in scan_ids
                for t, f in to_import[m].items()
            )
        print(f"  {min(start + BATCH, len(moon_ids))}/{len(moon_ids)}")
    print("done")


run(dry_run=os.environ.get("DRY_RUN") == "1")
