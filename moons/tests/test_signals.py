from unittest.mock import patch

from django.test import TestCase

from moons.models import OreTaxRates


class TestOreTaxRatesSignal(TestCase):
    def _make_profile(self):
        return OreTaxRates.objects.create(
            tag="test",
            ore_rate=10,
            ubiquitous_rate=10,
            common_rate=10,
            uncommon_rate=10,
            rare_rate=10,
            exceptional_rate=10,
        )

    @patch("moons.tasks.update_tax_prices.delay")
    def test_create_queues_tax_update(self, delay):
        with self.captureOnCommitCallbacks(execute=True):
            profile = self._make_profile()
        delay.assert_called_once_with(tax_id=profile.id)

    @patch("moons.tasks.update_tax_prices.delay")
    def test_edit_queues_tax_update(self, delay):
        profile = self._make_profile()
        with self.captureOnCommitCallbacks(execute=True):
            profile.rare_rate = 25
            profile.save()
        delay.assert_called_once_with(tax_id=profile.id)

    @patch("moons.tasks.update_tax_prices.delay")
    def test_nothing_queued_before_commit(self, delay):
        self._make_profile()
        delay.assert_not_called()
