from django.core.management.base import BaseCommand, CommandError

from corptools.tasks import update_or_create_map, process_ores_from_esi, update_ore_comp_table
from django_celery_beat.models import CrontabSchedule, PeriodicTask, IntervalSchedule
from corptools.models import MapSystem
from moons.models import OreTaxRates
from moons.tasks import update_ore_prices
from celery import chain


class Command(BaseCommand):
    help = 'Update Ore Price Data'

    def handle(self, *args, **options):
        self.stdout.write("Updating Ore Prices!")
        update_ore_prices()
        self.stdout.write("Complete!")
