from django.apps import AppConfig
from . import __version__


class MoonsConfig(AppConfig):
    name = 'moons'
    label = 'moons'

    verbose_name = f"Moons v{__version__}"
