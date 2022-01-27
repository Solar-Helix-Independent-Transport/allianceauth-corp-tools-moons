from django.core.management.base import BaseCommand, CommandError

from moons.models import InvoiceRecord
from moons.tasks import process_moons_from_esi
from corptools.models import MapRegion


class Command(BaseCommand):
    help = 'Print Tax Stats'

    def add_arguments(self, parser):
        parser.add_argument('region', type=str)

    def handle(self, *args, **options):

        self.stdout.write("Looking up region!")
        if MapRegion.objects.filter(name=options['region']).exists():
            self.stdout.write(
                f"Sending task to fetch Moons for {options['region']}")
            process_moons_from_esi.delay(
                [MapRegion.objects.filter(name=options['region']).first().region_id])
