from django.apps import AppConfig
from django.core.checks import Error, register

from . import __version__
from . import app_settings


class MoonsConfig(AppConfig):
    name = 'moons'
    label = 'moons'

    verbose_name = f"Moons v{__version__}"


@register()
def check_settings(app_configs, **kwargs):
    errors = []
    if app_settings.MOONS_ORE_RATE_BUCKET not in app_settings._valid_buckets:
        errors.append(Error(
            'Invalid MOONS_ORE_RATE_BUCKET',
            hint='Must be one of "weightedAverage", "max", "min", "stddev", "median", "percentile"',
            id='MOONS_ORE_RATE_BUCKET',
        ))
    if app_settings.MOONS_ORE_RATE_BUY_SELL not in app_settings._valid_buy_sell:
        errors.append(Error(
            'Invalid MOONS_ORE_RATE_BUY_SELL',
            hint="Must be 'buy' or 'sell'",
            id='MOONS_ORE_RATE_BUY_SELL',
        ))
    return errors
