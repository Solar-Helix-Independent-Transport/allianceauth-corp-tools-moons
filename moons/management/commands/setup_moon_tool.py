from django.core.management.base import BaseCommand, CommandError

from corptools.tasks import update_or_create_map, process_ores_from_esi, update_ore_comp_table
from corptools.models import MapSystem
from moons.models import OreTaxRates
from moons.tasks import update_ore_prices
from celery import chain


class Command(BaseCommand):
    help = 'Update or Populate Moon Dependent Data'

    def add_arguments(self, parser):
        parser.add_argument('--inline', action='store_true',
                            help='Run update in Console not via Celery')

    def handle(self, *args, **options):
        self.stdout.write("Creating DB models!")
        if OreTaxRates.objects.all().count() == 0:
            OreTaxRates.objects.create(
                tag="Ore Tax",
                ore_rate=0.2,
                ubiquitous_rate=0.2,
                common_rate=0.2,
                uncommon_rate=0.2,
                rare_rate=0.2,
                excptional_rate=0.2
            )
        systems = MapSystem.objects.all().count()
        if options['inline']:
            self.stdout.write("Running Tasks inline this may take some time!")
            if systems <= 8285:
                self.stdout.write("Starting Map Update")
                update_or_create_map()
            else:
                self.stdout.write("No map update needed.")
            self.stdout.write("Starting Asteroid Data Update")
            process_ores_from_esi()
            self.stdout.write("Starting Ore Comp Update")
            update_ore_comp_table()
            self.stdout.write("Starting Ore Price Tasks")
            update_ore_prices()
            self.stdout.write("Done!")
        else:
            que=[]
            self.stdout.write("Sending Tasks to celery for processing!")
            if systems <= 8285:
                self.stdout.write("Sending Map Update Task")
                que.append(update_or_create_map.si())
            else:
                self.stdout.write("No map update needed.")
            self.stdout.write("Sending Asteroid Data Task")
            que.append(process_ores_from_esi.si())
            self.stdout.write("Sending Ore Comp Task")
            que.append(update_ore_comp_table.si())
            self.stdout.write("Sending Ore Price Tasks")
            que.append(update_ore_prices.si())
            self.stdout.write("Tasks Queued!")
            chain(que).apply_async(priority=4)

