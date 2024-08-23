from django.core.management.base import BaseCommand

from moons.tasks import update_ore_prices


class Command(BaseCommand):
    help = 'Update Ore Price Data'

    def handle(self, *args, **options):
        self.stdout.write("Updating Ore Prices!")
        print(update_ore_prices())
        self.stdout.write("Complete!")
