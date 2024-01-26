from django.apps import apps
from django.conf import settings


def get_pub():
    out = getattr(settings, "PUBLIC_MOON_CORPS", [98609787])
    if isinstance(out, list):
        return out
    elif isinstance(out, int):
        return [out]
    elif isinstance(out, str):
        return [int(out)]


PUBLIC_MOON_CORPS = get_pub()  # trust


def discord_bot_active():
    if apps.is_installed("aadiscordbot"):
        import aadiscordbot as ab
        version = ab.__version__.split(".")
        if int(version[0]) >= 3:
            return True
    return False


def get_rental_discord_channel():
    out = getattr(settings, "MOON_RENTAL_CHANNEL", 373640301375651844)
    if isinstance(out, int):
        return out
    elif isinstance(out, str):
        return int(out)


MOONS_ORE_RATE_BUCKET = getattr(
    settings, "MOONS_ORE_RATE_BUCKET", "weightedAverage")
_valid_buckets = [
    "weightedAverage",
    "max",
    "min",
    "stddev",
    "median",
    "percentile"
]
MOONS_ORE_RATE_BUY_SELL = getattr(settings, "MOONS_ORE_RATE_BUY_SELL", "buy")
_valid_buy_sell = [
    "buy",
    "sell",
    "split"
]

MOONS_ENABLE_RENT_COG = getattr(settings, "MOONS_ENABLE_RENT_COG", True)
MOONS_LIMITED_FUTURE_REGIONS = getattr(
    settings, "MOONS_LIMITED_FUTURE_REGIONS", [])
MOONS_LIMITED_FUTURE_DAYS = getattr(settings, "MOONS_LIMITED_FUTURE_DAYS", 7)
