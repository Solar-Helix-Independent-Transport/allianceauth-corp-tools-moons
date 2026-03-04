

from django.test import TestCase

from moons.helpers import OreHelper
from moons.models import OreTaxRates
from moons.tasks import update_tax_prices


class TestInvoicesAccessPerms(TestCase):
    fixtures = ["moons_sde"]

    def setUp(cls):
        OreTaxRates.objects.create(
            tag="test_50",
            refine_rate=50,
            ore_rate=50,
            ubiquitous_rate=50,
            common_rate=50,
            uncommon_rate=50,
            rare_rate=50,
            exceptional_rate=50,
        )
        OreTaxRates.objects.create(
            tag="test_cascade",
            refine_rate=70,
            ore_rate=10,
            ubiquitous_rate=20,
            common_rate=30,
            uncommon_rate=40,
            rare_rate=50,
            exceptional_rate=60,
        )
        price_cache = {
            "Silicates": {"the_forge": 100},
            "Titanium": {"the_forge": 200},
            "Cadmium": {"the_forge": 300},
            "Thulium": {"the_forge": 400},
            "Hydrocarbons": {"the_forge": 500},
            "Scandium": {"the_forge": 1000},
            "Caesium": {"the_forge": 1100},
            "Vanadium": {"the_forge": 1200},
            "Tungsten": {"the_forge": 1300},
            "Pyerite": {"the_forge": 1400},
            "Mexallon": {"the_forge": 1500}
        }
        OreHelper.set_prices(price_cache)
        update_tax_prices()

    def test_ore_builder(self):
        ores = OreHelper.get_ore_array()
        self.assertEqual(len(ores), 5)

        self.assertEqual(len(ores[46319]['minerals']), 4)
        self.assertEqual(sum(list(ores[46319]['minerals'].values())), 144)

        self.assertEqual(len(ores[46309]['minerals']), 3)
        self.assertEqual(sum(list(ores[46309]['minerals'].values())), 150)

        self.assertEqual(len(ores[46301]['minerals']), 2)
        self.assertEqual(sum(list(ores[46301]['minerals'].values())), 100)

        self.assertEqual(len(ores[46295]['minerals']), 1)
        self.assertEqual(sum(list(ores[46295]['minerals'].values())), 80)

        self.assertEqual(len(ores[46285]['minerals']), 3)
        self.assertEqual(sum(list(ores[46285]['minerals'].values())), 12930)

    def test_full_prices(self):

        ores = OreHelper.get_ore_array_with_value_and_taxes()
        self.assertEqual(len(ores), 5)
        self.assertEqual(float(ores[46319]['value']), 356)
        self.assertEqual(float(ores[46309]['value']), 1450)
        self.assertEqual(float(ores[46301]['value']), 980)
        self.assertEqual(float(ores[46295]['value']), 1040)
        self.assertEqual(float(ores[46285]['value']), 180650)

        self.assertEqual(float(ores[46319]['tax']['test_50']), 89)
        self.assertEqual(float(ores[46309]['tax']['test_50']), 362.50)
        self.assertEqual(float(ores[46301]['tax']['test_50']), 245.00)
        self.assertEqual(float(ores[46295]['tax']['test_50']), 260.00)
        self.assertEqual(float(ores[46285]['tax']['test_50']), 45162.50)

        self.assertEqual(float(ores[46319]['tax']['test_cascade']), 149.52)
        self.assertEqual(float(ores[46309]['tax']['test_cascade']), 507.50)
        self.assertEqual(float(ores[46301]['tax']['test_cascade']), 274.40)
        self.assertEqual(float(ores[46295]['tax']['test_cascade']), 218.40)
        self.assertEqual(float(ores[46285]['tax']['test_cascade']), 25291)

    def test_minerals(self):
        ores = OreHelper.get_mineral_array()
        self.assertEqual(len(ores), 11)
        self.assertEqual(sum(ores), 149839)
