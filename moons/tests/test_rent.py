from decimal import Decimal
from unittest import mock

import requests

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from moons.models import OreTaxRates
from moons.rent import (
    FuelPricesUnavailable, cached_fuel_prices, fetch_fuel_prices, fuel_for,
    metenox_fuel_30d, rent_breakdown,
)


def _profile(**kwargs):
    defaults = dict(tag="Rent", refine_rate=Decimal("87.5"), ore_rate=0, ubiquitous_rate=0,
                    common_rate=0, uncommon_rate=0, rare_rate=0, exceptional_rate=0)
    return OreTaxRates(**{**defaults, **kwargs})


class TestMetenoxFuel(SimpleTestCase):
    def test_fuel_for_30_days_at_200_gas_and_5_blocks_an_hour(self):
        fuel = metenox_fuel_30d(gas_price=5000, block_prices={"A": 20000, "B": 22000}, gas_factor=2)

        # gas 5,000 * 720 h * 200 = 720,000,000; blocks avg 21,000 * 720 * 5 = 75,600,000
        self.assertEqual(fuel.gas_30d, 720_000_000)
        self.assertEqual(fuel.blocks_30d, 75_600_000)
        self.assertEqual(fuel.total_30d, 795_600_000)

    def test_gas_above_soft_cap_is_softened_by_gas_factor(self):
        fuel = metenox_fuel_30d(gas_price=14000, block_prices={"A": 20000}, gas_factor=2)

        # 10,000 + (14,000 - 10,000) / 2 = 12,000
        self.assertEqual(fuel.gas_adjusted, 12000)
        self.assertEqual(fuel.gas_30d, 12000 * 720 * 200)

    @override_settings(MOONS_METENOX_GAS_PER_HOUR=110)
    def test_gas_rate_setting(self):
        fuel = metenox_fuel_30d(gas_price=5000, block_prices={"A": 20000}, gas_factor=2)

        self.assertEqual(fuel.gas_30d, 5000 * 720 * 110)

    @override_settings(MOONS_FUEL_BUY_SELL="sell", MOONS_FUEL_BUCKET="min")
    def test_fetch_reads_configured_bucket_from_fuzzwork(self):
        payload = {str(t): {"sell": {"min": str(p)}} for t, p in (
            (81143, 9000), (4312, 20000), (4246, 21000), (4247, 22000), (4051, 23000))}
        with mock.patch("moons.rent.requests.get") as get:
            get.return_value.json.return_value = payload
            gas, blocks = fetch_fuel_prices()

        self.assertIn("region=10000002", get.call_args.args[0])
        self.assertEqual(gas, 9000)
        self.assertEqual(sorted(blocks.values()), [20000, 21000, 22000, 23000])


class TestRentBreakdown(SimpleTestCase):
    FUEL = metenox_fuel_30d(gas_price=5000, block_prices={"A": 21000}, gas_factor=2)  # 795.6m

    def test_profile_without_rent_options_is_tax_rounded(self):
        rent = rent_breakdown(Decimal("144576000"), _profile(), self.FUEL)

        self.assertIsNone(rent.fuel)
        self.assertEqual(rent.final, 145_000_000)

    def test_fuel_share_and_rounding(self):
        profile = _profile(rent_subtract_metenox_fuel=True, rent_profit_share=Decimal("65"))

        rent = rent_breakdown(Decimal("2000000000"), profile, self.FUEL)

        # (2,000,000,000 - 795,600,000) * 0.65 = 782,860,000 -> 783,000,000
        self.assertEqual(rent.profit, Decimal("1204400000"))
        self.assertEqual(rent.rounded, 783_000_000)
        self.assertEqual(rent.final, 783_000_000)

    def test_minimum_rent(self):
        profile = _profile(rent_subtract_metenox_fuel=True, rent_profit_share=Decimal("65"),
                           rent_minimum=100_000_000)

        rent = rent_breakdown(Decimal("900000000"), profile, self.FUEL)

        # (900m - 795.6m) * 0.65 = 67.86m -> 68m, raised to the 100m minimum
        self.assertEqual(rent.rounded, 68_000_000)
        self.assertEqual(rent.final, 100_000_000)


class TestCachedFuelPrices(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_fetched_once_then_cached(self):
        with mock.patch("moons.rent.fetch_fuel_prices", return_value=(9000, {"A": 20000})) as fetch:
            first = cached_fuel_prices()
            second = cached_fuel_prices()

        self.assertEqual(first, (9000, {"A": 20000}))
        self.assertEqual(second, first)
        fetch.assert_called_once()

    def test_fuzzwork_failure_is_unavailable_and_not_cached(self):
        with mock.patch("moons.rent.fetch_fuel_prices", side_effect=requests.ConnectionError):
            with self.assertRaises(FuelPricesUnavailable):
                cached_fuel_prices()
        with mock.patch("moons.rent.fetch_fuel_prices", return_value=(9000, {"A": 20000})):
            self.assertEqual(cached_fuel_prices()[0], 9000)

    def test_no_fuel_for_profile_that_does_not_subtract_it(self):
        with mock.patch("moons.rent.fetch_fuel_prices") as fetch:
            self.assertIsNone(fuel_for(_profile()))
        fetch.assert_not_called()
