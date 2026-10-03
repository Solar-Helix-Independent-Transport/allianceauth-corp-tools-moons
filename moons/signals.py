import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import OreTaxRates

logger = logging.getLogger(__name__)


@receiver(post_save, sender=OreTaxRates)
def ore_tax_rates_saved(sender, instance, **kwargs):
    """Rebuild the per-ore tax prices for a profile whenever its rates change."""
    try:
        from .tasks import update_tax_prices
        tax_id = instance.id
        transaction.on_commit(lambda: update_tax_prices.delay(tax_id=tax_id))
    except Exception as e:
        logger.error(f"Failed to queue tax price update for OreTaxRates {instance.id}: {e}")
