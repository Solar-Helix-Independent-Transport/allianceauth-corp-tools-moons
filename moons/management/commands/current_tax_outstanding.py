from django.core.management.base import BaseCommand, CommandError

from moons.models import InvoiceRecord
from moons.tasks import update_ore_prices


class Command(BaseCommand):
    help = 'Print Tax Stats'


    def handle(self, *args, **options):
        self.stdout.write("Calculating!")
        last_date = InvoiceRecord.get_last_invoice_date()
        self.stdout.write(f"Last Invoice {last_date}!")
        self.stdout.write("Doing some math... Please wait...\n\n")
        accounts_seen = 0
        locations = set()
        data = InvoiceRecord.generate_invoice_data()
        total_mined = 0
        total_taxed = 0
        # run known people
        for u, d in data['knowns'].items():
            try:
                total_mined += d['total_value']
                total_taxed += d['tax_value']

                accounts_seen += 1
                for l in d['locations']:
                    locations.add(l)
            except KeyError:
                pass # probably wanna ping admin about it.
        
        for u, d in data['unknowns'].items():
            try:
                total_mined += d['totals_isk']
                total_taxed += d['tax_isk']
                for l in d['seen_at']:
                    locations.add(l)
            except KeyError:
                pass # probably wanna ping admin about it.

        self.stdout.write(f"We've seen {accounts_seen} known members!")
        self.stdout.write(f"We've seen { len(data['unknowns']) } unknown characters!\n\n")
        self.stdout.write(f"Who have mined ${total_mined:,} worth of ore!")
        self.stdout.write(f"Current Tax puts this at ${total_taxed:,} in taxes!\n\n")
        structures = "\n ".join(list(locations))
        self.stdout.write(f"the structures included are:\n { structures }")

        


