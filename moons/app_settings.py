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
    return 'aadiscordbot' in settings.INSTALLED_APPS


def get_rental_discord_channel():
    out = getattr(settings, "MOON_RENTAL_CHANNEL", 373640301375651844)
    if isinstance(out, int):
        return out
    elif isinstance(out, str):
        return int(out)
