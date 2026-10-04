"""Suggested rent: a profile's 30 day tax, less Metenox fuel if the profile says so,
times its profit share, rounded, with a minimum. Moon Values, the New Rental
suggestion and the Discord commands all price rent this way."""
from dataclasses import dataclass
from decimal import Decimal

import requests

from django.core.cache import cache

from . import app_settings

HOURS_30D = 720
FUEL_MARKET_REGION_ID = 10000002  # The Forge
GAS_TYPE_ID = 81143  # Magmatic Gas
FUEL_BLOCK_TYPE_IDS = {
    4312: "Oxygen Fuel Block",
    4246: "Hydrogen Fuel Block",
    4247: "Helium Fuel Block",
    4051: "Nitrogen Fuel Block",
}
GAS_SOFT_CAP = 10000
BLOCKS_PER_HOUR = 5
FUEL_PRICES_CACHE_KEY = "moons:metenox_fuel_prices"
FUEL_PRICES_CACHE_SECONDS = 60 * 60


class FuelPricesUnavailable(Exception):
    pass


@dataclass
class MetenoxFuel:
    gas_price: float
    gas_adjusted: float
    block_prices: dict
    block_average: float
    gas_per_hour: int
    gas_30d: float
    blocks_30d: float

    @property
    def total_30d(self):
        return self.gas_30d + self.blocks_30d


def fetch_fuel_prices():
    """Jita magmatic gas and fuel block prices from Fuzzwork."""
    type_ids = [GAS_TYPE_ID, *FUEL_BLOCK_TYPE_IDS]
    prices = requests.get(
        "https://market.fuzzwork.co.uk/aggregates/"
        f"?region={FUEL_MARKET_REGION_ID}&types={','.join(str(t) for t in type_ids)}",
        timeout=30,
    ).json()
    buy_sell, bucket = app_settings.fuel_buy_sell(), app_settings.fuel_bucket()
    gas = float(prices[str(GAS_TYPE_ID)][buy_sell][bucket])
    blocks = {
        name: float(prices[str(type_id)][buy_sell][bucket])
        for type_id, name in FUEL_BLOCK_TYPE_IDS.items()
    }
    return gas, blocks


def cached_fuel_prices():
    """fetch_fuel_prices, kept for an hour so pages and commands agree and Fuzzwork isn't hit per request."""
    prices = cache.get(FUEL_PRICES_CACHE_KEY)
    if prices is None:
        try:
            prices = fetch_fuel_prices()
        except (requests.RequestException, KeyError, TypeError, ValueError) as e:
            raise FuelPricesUnavailable("Couldn't get Metenox fuel prices from Fuzzwork") from e
        cache.set(FUEL_PRICES_CACHE_KEY, prices, FUEL_PRICES_CACHE_SECONDS)
    return prices


def fuel_for(tax_rate):
    """30 days of Metenox fuel when the profile subtracts it, else None."""
    if not tax_rate.rent_subtract_metenox_fuel:
        return None
    return metenox_fuel_30d(*cached_fuel_prices())


def metenox_fuel_30d(gas_price, block_prices, gas_factor=None):
    gas_factor = gas_factor or app_settings.fuel_gas_factor()
    gas_adjusted = gas_price
    if gas_adjusted > GAS_SOFT_CAP:
        # soften gas price spikes
        gas_adjusted = GAS_SOFT_CAP + (gas_price - GAS_SOFT_CAP) / gas_factor
    block_average = sum(block_prices.values()) / len(block_prices)
    gas_per_hour = app_settings.metenox_gas_per_hour()
    return MetenoxFuel(
        gas_price, gas_adjusted, block_prices, block_average, gas_per_hour,
        gas_30d=gas_adjusted * HOURS_30D * gas_per_hour,
        blocks_30d=block_average * HOURS_30D * BLOCKS_PER_HOUR,
    )


@dataclass
class RentBreakdown:
    tax_30d: Decimal
    fuel: object  # MetenoxFuel, or None when the profile doesn't subtract fuel
    profit: Decimal
    share: Decimal  # percent
    raw: Decimal
    rounded: int
    minimum: int
    final: int


def rent_breakdown(tax_30d, tax_rate, fuel=None):
    fuel = fuel if tax_rate.rent_subtract_metenox_fuel else None
    profit = Decimal(tax_30d) - (Decimal(str(fuel.total_30d)) if fuel else 0)
    share = Decimal(tax_rate.rent_profit_share)
    raw = profit * share / 100
    rounded = int(round(raw, -6))
    minimum = tax_rate.rent_minimum
    return RentBreakdown(Decimal(tax_30d), fuel, profit, share, raw, rounded, minimum,
                         max(rounded, minimum))
