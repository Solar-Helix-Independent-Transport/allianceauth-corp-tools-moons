from django.core.management.base import BaseCommand, CommandError

from corptools.tasks import update_or_create_map, process_ores_from_esi, update_ore_comp_table
from django_celery_beat.models import CrontabSchedule, PeriodicTask, IntervalSchedule
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
                exceptional_rate=0.2
            )
        self.stdout.write("Setting up Periodic Tasks!")
        schedule_bi_weekly, _ = IntervalSchedule.objects.get_or_create(every=14, 
                        period=IntervalSchedule.DAYS)
        schedule_20_min, _ = CrontabSchedule.objects.get_or_create(minute='10,30,50',
                                                                    hour='*',
                                                                    day_of_week='*',
                                                                    day_of_month='*',
                                                                    month_of_year='*',
                                                                    timezone='UTC'
                                                                    )
        
        schedule_start_of_month, _ = CrontabSchedule.objects.get_or_create(minute='0',
                                                                    hour='0',
                                                                    day_of_week='*',
                                                                    day_of_month='1',
                                                                    month_of_year='*',
                                                                    timezone='UTC'
                                                                    )
        
        task_obs= PeriodicTask.objects.update_or_create(
            task='moons.tasks.run_obs_for_all_corps',
            defaults={
                'crontab': schedule_20_min,
                'interval': None,
                'solar': None,
                'name': 'Moon Obs Updates',
                'enabled': True
            }
        )
        task_prices= PeriodicTask.objects.update_or_create(
            task='moons.tasks.update_ore_prices',
            defaults={
                'crontab': schedule_start_of_month,
                'interval': None,
                'solar': None,
                'name': 'Moon Ore Prices',
                'enabled': True
            }
        )
        task_invoice= PeriodicTask.objects.update_or_create(
            task='moons.tasks.generate_taxes',
            defaults={
                'interval': schedule_bi_weekly,
                'crontab': None,
                'solar': None,
                'name': 'Send Moon Invoices',
                'enabled': False
            }
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

