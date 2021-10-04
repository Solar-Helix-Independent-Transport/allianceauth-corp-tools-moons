from django.conf import settings

PUBLIC_MOON_CORPS = getattr(settings, "PUBLIC_MOON_CORPS", [98609787]) # trust

def discord_bot_active():
    return 'aadiscordbot' in settings.INSTALLED_APPS
