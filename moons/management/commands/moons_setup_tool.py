from celery import chain
from django_celery_beat.models import (
    CrontabSchedule, IntervalSchedule, PeriodicTask,
)

from django.core.management.base import BaseCommand, CommandError

from moons.models import OreTaxRates
from moons.tasks import update_ore_prices


class Command(BaseCommand):
    help = 'Update or Populate Moon Dependent Data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--inline',
            action='store_true',
            help='Run update in Console not via Celery'
        )

    def handle(self, *args, **options):
        self.stdout.write("Creating DB models!")
        if OreTaxRates.objects.all().count() == 0:
            OreTaxRates.objects.create(
                tag="Ore Tax",
                ore_rate=20,
                ubiquitous_rate=20,
                common_rate=20,
                uncommon_rate=20,
                rare_rate=20,
                exceptional_rate=20
            )
        self.stdout.write("Setting up Periodic Tasks!")
        schedule_bi_weekly, _ = IntervalSchedule.objects.get_or_create(
            every=14,
            period=IntervalSchedule.DAYS
        )
        schedule_30_min, _ = CrontabSchedule.objects.get_or_create(
            minute='30',
            hour='*',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone='UTC'
        )

        schedule_start_of_month, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='0',
            day_of_week='*',
            day_of_month='1',
            month_of_year='*',
            timezone='UTC'
        )

        task_obs = PeriodicTask.objects.update_or_create(
            task='moons.tasks.run_obs_for_all_corps',
            defaults={
                'crontab': schedule_30_min,
                'interval': None,
                'solar': None,
                'name': 'Moon Obs Updates',
                'enabled': True
            }
        )
        task_frack = PeriodicTask.objects.update_or_create(
            task='moons.tasks.process_moon_pulls',
            defaults={
                'crontab': schedule_30_min,
                'interval': None,
                'solar': None,
                'name': 'Moon Frack Updates',
                'enabled': True
            }
        )
        task_prices = PeriodicTask.objects.update_or_create(
            task='moons.tasks.update_ore_prices',
            defaults={
                'crontab': schedule_start_of_month,
                'interval': None,
                'solar': None,
                'name': 'Moon Ore Prices',
                'enabled': True
            }
        )
        task_invoice = PeriodicTask.objects.update_or_create(
            task='moons.tasks.generate_taxes',
            defaults={
                'interval': schedule_bi_weekly,
                'crontab': None,
                'solar': None,
                'name': 'Send Moon Invoices',
                'enabled': False
            }
        )

        if options['inline']:
            self.stdout.write("Starting Ore Price Updates")
            update_ore_prices()
            self.stdout.write("Done!")
        else:
            que = []
            self.stdout.write("Sending Ore Price Task!")
            que.append(update_ore_prices.si())
            self.stdout.write("Task Queued!")
            chain(que).apply_async(priority=4)
