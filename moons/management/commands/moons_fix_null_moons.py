from django.core.management.base import BaseCommand

from moons.models import MiningObservation, MoonFrack
from corptools.models import EveLocation


class Command(BaseCommand):
    help = 'Fix null Observation Data'

    def handle(self, *args, **options):
        self.stdout.write("Finding dirty Observation Data!")
        obs = MiningObservation.objects.filter(moon__isnull=True)
        structures = obs.values_list("observing_id", flat=True).distinct()
        self.stdout.write(f"Found {structures.count()} structures to fix")
        for s in structures:
            st = EveLocation.objects.get(location_id=s)
            self.stdout.write(f"Checking {st.location_name}")
            mf = MoonFrack.objects.filter(
                structure_id=s, moon_name__isnull=False)
            if mf.exists():
                moon = mf.last().moon_name
                self.stdout.write(
                    f"    Found {moon} for {st.location_name} updating all observations")
                MiningObservation.objects.filter(
                    moon__isnull=True,
                    observing_id=s
                ).update(
                    moon=moon
                )
                self.stdout.write(f"    {st.location_name} Completed")
            else:
                self.stdout.write(f"    Moon Not Found!")
