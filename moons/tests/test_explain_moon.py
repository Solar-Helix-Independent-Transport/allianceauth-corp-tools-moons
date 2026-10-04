from decimal import Decimal

from eve_sde.models import (
    Constellation, ItemGroup, ItemType, Moon, Region, SolarSystem,
)

from django.test import TestCase
from django.utils import timezone

from allianceauth.tests.auth_utils import AuthUtils

from moons.explain import explain_moon
from moons.models import MoonScan, OrePrice, OreTax, OreTaxRates
from moons.rent import metenox_fuel_30d
from moons.scans import moon_values

MOON_1 = 40161465
CINNABAR = 45506
BITUMENS = 45492


class TestExplainMoon(TestCase):
    """Same moon as TestMoonValues: 1,440,000 units of each ore at 50%."""

    @classmethod
    def setUpTestData(cls):
        region = Region.objects.create(id=10000001, name="Test Region")
        constellation = Constellation.objects.create(id=20000001, name="Test Constellation", region=region)
        system = SolarSystem.objects.create(id=30002542, name="Auga", constellation=constellation)
        moon = Moon.objects.create(id=MOON_1, name="Auga V - Moon 1", solar_system=system)
        rare = ItemGroup.objects.create(id=1922, name="Rare Moon Asteroids")
        ubiq = ItemGroup.objects.create(id=1884, name="Ubiquitous Moon Asteroids")
        cinnabar = ItemType.objects.create(id=CINNABAR, name="Cinnabar", group=rare)
        bitumens = ItemType.objects.create(id=BITUMENS, name="Bitumens", group=ubiq)
        cls.profile = OreTaxRates.objects.create(
            tag="Rental", refine_rate=Decimal("87.5"), ore_rate=0, ubiquitous_rate=10,
            common_rate=0, uncommon_rate=0, rare_rate=20, exceptional_rate=0,
            show_in_moon_values=True, rent_profit_share=50, rent_minimum=100_000_000)
        OrePrice.objects.create(item=cinnabar, price=Decimal("1000"))
        OrePrice.objects.create(item=bitumens, price=Decimal("100"))
        OreTax.objects.create(item=cinnabar, tax=cls.profile, price=Decimal("175"))
        # stale: 87.5 x 10% is 8.75
        OreTax.objects.create(item=bitumens, tax=cls.profile, price=Decimal("5"))
        scan = MoonScan.objects.create(moon=moon, added_by=AuthUtils.create_user("valuer"), added_at=timezone.now())
        scan.ores.create(ore_id=CINNABAR, fraction=Decimal("0.5"))
        scan.ores.create(ore_id=BITUMENS, fraction=Decimal("0.5"))

    def _explain(self, fuel=None):
        [v] = moon_values(self.profile)
        return "\n".join(explain_moon(v, self.profile, fuel))

    def test_works_each_ore_from_price_to_30_day_tax(self):
        text = self._explain()

        self.assertIn("Cinnabar (45506) - rare_rate 20%", text)
        self.assertIn("50.00% x 2,880,000 = 1,440,000 units", text)
        self.assertIn("Value  = 1,000.00 x 87.5% = Ƶ875.00/unit", text)
        self.assertIn("OreTax = 875.00 x 20% = Ƶ175.00/unit", text)
        self.assertIn("30d tax   1,440,000 x 175.00 = Ƶ252,000,000", text)

    def test_flags_stored_ore_tax_that_no_longer_matches_prices(self):
        text = self._explain()

        bitumens = text[text.index("Bitumens (45492)"):]
        self.assertIn("OreTax = 87.50 x 10% = Ƶ8.75/unit", bitumens)
        self.assertIn("Stored OreTax used: Ƶ5.00/unit", bitumens)
        self.assertIn("!! Stored OreTax differs", bitumens)
        self.assertEqual(text.count("!! Stored OreTax differs"), 1)

    def test_rent_without_fuel_is_share_of_tax_rounded(self):
        text = self._explain()

        # tax 252,000,000 + 7,200,000; 50% = 129,600,000
        self.assertIn("Not subtracted by this profile", text)
        self.assertIn("Tax 30d                  Ƶ259,200,000", text)
        self.assertIn("Rent   = 259,200,000 x 50% = Ƶ129,600,000", text)
        self.assertIn("Suggested rent           Ƶ130,000,000", text)

    def test_rent_with_fuel_shows_fuel_working_and_profit(self):
        self.profile.rent_subtract_metenox_fuel = True
        fuel = metenox_fuel_30d(gas_price=14000, block_prices={"A": 20000}, gas_factor=2)

        text = self._explain(fuel)

        # gas 12,000 x 720 x 200 = 1,728,000,000 is more than the tax: minimum applies
        self.assertIn("10,000 + (14,000.00 - 10,000) / ", text)
        self.assertIn("Fuel 30d = 1,728,000,000 + 72,000,000 = Ƶ1,800,000,000", text)
        self.assertIn("Profit = 259,200,000 - 1,800,000,000 fuel = Ƶ-1,540,800,000", text)
        self.assertIn("Suggested rent           Ƶ100,000,000", text)
