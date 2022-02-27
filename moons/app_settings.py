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
