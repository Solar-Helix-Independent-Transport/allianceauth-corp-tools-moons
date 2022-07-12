from django.test import TestCase
from corptools.models import EveItemType, InvTypeMaterials, EveItemCategory, EveItemGroup
from moons.helpers import OreHelper
from moons.models import OreTaxRates
from moons.tasks import update_tax_prices


class TestInvoicesAccessPerms(TestCase):
    def setUp(cls):
        EveItemCategory.objects.create(category_id=25, name="Asteroid")

        EveItemGroup.objects.create(
            group_id=1923, category_id=25, name="Exceptional Moon Asteroids")
        EveItemGroup.objects.create(
            group_id=1922, category_id=25, name="Rare Moon Asteroids")
        EveItemGroup.objects.create(
            group_id=1921, category_id=25, name="Uncommon Moon Asteroids")
        EveItemGroup.objects.create(
            group_id=1920, category_id=25, name="Common Moon Asteroids")
        EveItemGroup.objects.create(
            group_id=1884, category_id=25, name="Ubiquitous Moon Asteroids")

        EveItemType.objects.create(
            type_id=1,
            name="Mineral 1",
            description="Mineral 1",
            portion_size=1,
            published=True
        )
        EveItemType.objects.create(
            type_id=2,
            name="Mineral 2",
            description="Mineral 2",
            portion_size=1,
            published=True
        )
        EveItemType.objects.create(
            type_id=3,
            name="Mineral 3",
            description="Mineral 3",
            portion_size=1,
            published=True
        )
        EveItemType.objects.create(
            type_id=4,
            name="Mineral 4",
            description="Mineral 4",
            portion_size=1,
            published=True
        )
        EveItemType.objects.create(
            type_id=5,
            name="Mineral 5",
            description="Mineral 5",
            portion_size=1,
            published=True
        )
        EveItemType.objects.create(
            type_id=6,
            name="Mineral 6",
            description="Mineral 6",
            portion_size=1,
            published=True
        )

        EveItemType.objects.create(
            type_id=46319,
            name="Exceptional",
            description="Test Exceptional Ore",
            group_id=1923,
            portion_size=100,
            published=True,
            volume=1000
        )
        # 40	1	46319	46319	1
        InvTypeMaterials.objects.create(
            type_id=46319,
            eve_type_id=46319,
            material_type_id=1,
            met_type_id=1,
            qty=40
        )
        # 40	2	46319	46319	2
        InvTypeMaterials.objects.create(
            type_id=46319,
            eve_type_id=46319,
            material_type_id=2,
            met_type_id=2,
            qty=40
        )
        # 20	3	46319	46319	3
        InvTypeMaterials.objects.create(
            type_id=46319,
            eve_type_id=46319,
            material_type_id=3,
            met_type_id=3,
            qty=20
        )
        # 44	4	46319	46319	4
        InvTypeMaterials.objects.create(
            type_id=46319,
            eve_type_id=46319,
            material_type_id=4,
            met_type_id=4,
            qty=44
        )

        EveItemType.objects.create(
            type_id=46309,
            name="Rare",
            description="Test Rare Ore",
            group_id=1922,
            portion_size=100,
            published=True,
            volume=5000
        )
        # 30	6	46309	46309	6
        InvTypeMaterials.objects.create(
            type_id=46309,
            eve_type_id=46309,
            material_type_id=6,
            met_type_id=6,
            qty=30
        )
        # 20	5	46309	46309	5
        InvTypeMaterials.objects.create(
            type_id=46309,
            eve_type_id=46309,
            material_type_id=5,
            met_type_id=5,
            qty=20
        )
        # 100	3	46309	46309	3
        InvTypeMaterials.objects.create(
            type_id=46309,
            eve_type_id=46309,
            material_type_id=3,
            met_type_id=3,
            qty=100
        )

        EveItemType.objects.create(
            type_id=46301,
            name="Uncommon",
            description="Test Uncommon Ore",
            group_id=1921,
            portion_size=100,
            published=True,
            volume=5000
        )
        # 45	1	46301	46301	1
        InvTypeMaterials.objects.create(
            type_id=46301,
            eve_type_id=46301,
            material_type_id=1,
            met_type_id=1,
            qty=45
        )
        # 25	2	46301	46301	2
        InvTypeMaterials.objects.create(
            type_id=46301,
            eve_type_id=46301,
            material_type_id=2,
            met_type_id=2,
            qty=25
        )

        EveItemType.objects.create(
            type_id=46295,
            name="Common",
            description="Test Common Ore",
            group_id=1920,
            portion_size=100,
            published=True,
            volume=5000
        )
        # 500	5	46295	46295	5
        InvTypeMaterials.objects.create(
            type_id=46295,
            eve_type_id=46295,
            material_type_id=5,
            met_type_id=5,
            qty=500
        )

        EveItemType.objects.create(
            type_id=46285,
            name="Ubiquitous",
            description="Test Ubiquitous Ore",
            group_id=1884,
            portion_size=100,
            published=True,
            volume=5000
        )
        # 50	1	46285	46285	1
        InvTypeMaterials.objects.create(
            type_id=46285,
            eve_type_id=46285,
            material_type_id=5,
            met_type_id=5,
            qty=50
        )
        # 25	2	46285	46285	2
        InvTypeMaterials.objects.create(
            type_id=46285,
            eve_type_id=46285,
            material_type_id=2,
            met_type_id=2,
            qty=25
        )

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

    def test_ore_builder(self):
        ores = OreHelper.get_ore_array()
        self.assertEquals(len(ores), 5)

        self.assertEquals(len(ores[46319]['minerals']), 4)
        self.assertEquals(sum(list(ores[46319]['minerals'].values())), 144)

        self.assertEquals(len(ores[46309]['minerals']), 3)
        self.assertEquals(sum(list(ores[46309]['minerals'].values())), 150)

        self.assertEquals(len(ores[46301]['minerals']), 2)
        self.assertEquals(sum(list(ores[46301]['minerals'].values())), 70)

        self.assertEquals(len(ores[46295]['minerals']), 1)
        self.assertEquals(sum(list(ores[46295]['minerals'].values())), 500)

        self.assertEquals(len(ores[46285]['minerals']), 2)
        self.assertEquals(sum(list(ores[46285]['minerals'].values())), 75)

    def test_full_prices(self):
        price_cache = {
            "Mineral 1": {"the_forge": 100},
            "Mineral 2": {"the_forge": 200},
            "Mineral 3": {"the_forge": 300},
            "Mineral 4": {"the_forge": 400},
            "Mineral 5": {"the_forge": 500},
            "Mineral 6": {"the_forge": 1000}
        }
        OreHelper.set_prices(price_cache)
        update_tax_prices()

        ores = OreHelper.get_ore_array_with_value_and_taxes()

        self.assertEquals(len(ores), 5)
        self.assertEquals(float(ores[46319]['value']), 356)
        self.assertEquals(float(ores[46309]['value']), 700)
        self.assertEquals(float(ores[46301]['value']), 95)
        self.assertEquals(float(ores[46295]['value']), 2500)
        self.assertEquals(float(ores[46285]['value']), 300)

        self.assertEquals(float(ores[46319]['tax']['test_50']), 89)
        self.assertEquals(float(ores[46309]['tax']['test_50']), 175)
        self.assertEquals(float(ores[46301]['tax']['test_50']), 23.75)
        self.assertEquals(float(ores[46295]['tax']['test_50']), 625)
        self.assertEquals(float(ores[46285]['tax']['test_50']), 75)

        self.assertEquals(float(ores[46319]['tax']['test_cascade']), 149.52)
        self.assertEquals(float(ores[46309]['tax']['test_cascade']), 245)
        self.assertEquals(float(ores[46301]['tax']['test_cascade']), 26.60)
        self.assertEquals(float(ores[46295]['tax']['test_cascade']), 525)
        self.assertEquals(float(ores[46285]['tax']['test_cascade']), 42)

    def test_minerals(self):
        ores = OreHelper.get_mineral_array()
        self.assertEquals(len(ores), 6)
        self.assertEquals(sum(ores), 21)
