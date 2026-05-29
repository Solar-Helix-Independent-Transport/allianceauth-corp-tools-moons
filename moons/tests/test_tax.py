from datetime import timedelta

from corptools.models import CorporationAudit, EveLocation, EveName
from eve_sde.models import ItemType

from django.test import TestCase
from django.utils import timezone

from allianceauth.eveonline.models import EveCorporationInfo

from moons.models import (
    MiningObservation, MiningTax, OrePrice, OreTax, OreTaxRates,
)


def _make_observation(corp_audit, structure, char_name, ore_type, quantity, last_updated):
    pk = MiningObservation.build_pk(
        corp_id=corp_audit.corporation.corporation_id,
        observer_id=structure.location_id,
        observed_character_id=char_name.eve_id,
        ob_date=last_updated,
        type_id=ore_type.pk,
    )
    return MiningObservation.objects.create(
        ob_pk=pk,
        observing_corporation=corp_audit,
        observing_id=structure.location_id,
        structure=structure,
        character_name=char_name,
        character_id=char_name.eve_id,
        last_updated=last_updated,
        quantity=quantity,
        recorded_corporation_id=corp_audit.corporation.corporation_id,
        type_name=ore_type,
        type_id=ore_type.pk,
    )


class TestFlatTaxMoons(TestCase):
    fixtures = ["moons_sde"]

    def setUp(self):
        corp_info = EveCorporationInfo.objects.create(
            corporation_id=1, corporation_name="Test Corp",
            corporation_ticker="TST", member_count=10, ceo_id=1,
        )
        self.corp_audit = CorporationAudit.objects.create(corporation=corp_info)
        self.structure = EveLocation.objects.create(
            location_id=1000000, location_name="Test Refinery"
        )
        self.char = EveName.objects.create(
            eve_id=9001, name="Test Miner", category="character"
        )
        self.ore_type = ItemType.objects.get(pk=46295)
        OrePrice.objects.create(item=self.ore_type, price=100, goo_only=False)

        MiningTax.objects.create(use_variable_tax=False, flat_tax_rate=0.10, rank=1)

        self.start = timezone.now() - timedelta(days=30)
        self.end = timezone.now() + timedelta(days=1)

        _make_observation(
            self.corp_audit, self.structure, self.char,
            self.ore_type, quantity=1000, last_updated=timezone.now(),
        )

    def test_player_present_in_output(self):
        result = MiningObservation.tax_moons(self.start, self.end)
        self.assertIn(9001, result['player_data'])

    def test_isk_value_calculated(self):
        result = MiningObservation.tax_moons(self.start, self.end)
        self.assertAlmostEqual(result['player_data'][9001]['totals_isk'], 100 * 1000)

    def test_flat_tax_rate_applied(self):
        result = MiningObservation.tax_moons(self.start, self.end)
        self.assertAlmostEqual(result['player_data'][9001]['tax_isk'], 10_000.0)

    def test_seen_at_contains_structure_name(self):
        result = MiningObservation.tax_moons(self.start, self.end)
        self.assertIn("Test Refinery", result['player_data'][9001]['seen_at'])

    def test_observation_outside_window_excluded(self):
        old_char = EveName.objects.create(eve_id=9002, name="Old Miner", category="character")
        old_date = timezone.now() - timedelta(days=60)
        _make_observation(
            self.corp_audit, self.structure, old_char,
            self.ore_type, quantity=1000, last_updated=old_date,
        )
        window_start = timezone.now() - timedelta(days=7)
        result = MiningObservation.tax_moons(window_start, self.end)
        self.assertNotIn(9002, result['player_data'])

    def test_multiple_characters_accumulate_separately(self):
        char2 = EveName.objects.create(eve_id=9003, name="Second Miner", category="character")
        structure2 = EveLocation.objects.create(location_id=1000001, location_name="Refinery 2")
        _make_observation(
            self.corp_audit, structure2, char2,
            self.ore_type, quantity=500, last_updated=timezone.now(),
        )
        result = MiningObservation.tax_moons(self.start, self.end)
        self.assertIn(9001, result['player_data'])
        self.assertIn(9003, result['player_data'])
        self.assertAlmostEqual(result['player_data'][9001]['totals_isk'], 100_000.0)
        self.assertAlmostEqual(result['player_data'][9003]['totals_isk'], 50_000.0)


class TestRankDeduplication(TestCase):
    fixtures = ["moons_sde"]

    def setUp(self):
        corp_info = EveCorporationInfo.objects.create(
            corporation_id=2, corporation_name="Rank Corp",
            corporation_ticker="RNK", member_count=1, ceo_id=1,
        )
        self.corp_audit = CorporationAudit.objects.create(corporation=corp_info)
        self.structure = EveLocation.objects.create(
            location_id=2000000, location_name="Rank Refinery"
        )
        self.char = EveName.objects.create(
            eve_id=9010, name="Rank Miner", category="character"
        )
        self.ore_type = ItemType.objects.get(pk=46295)
        OrePrice.objects.create(item=self.ore_type, price=100, goo_only=False)

        # Higher rank rule (applied first) at 10%
        MiningTax.objects.create(use_variable_tax=False, flat_tax_rate=0.10, rank=10)
        # Lower rank rule at 20% — should never apply to the same structure
        MiningTax.objects.create(use_variable_tax=False, flat_tax_rate=0.20, rank=5)

        self.start = timezone.now() - timedelta(days=30)
        self.end = timezone.now() + timedelta(days=1)

        _make_observation(
            self.corp_audit, self.structure, self.char,
            self.ore_type, quantity=1000, last_updated=timezone.now(),
        )

    def test_structure_only_taxed_by_highest_rank(self):
        result = MiningObservation.tax_moons(self.start, self.end)
        # If both rules applied: 10% + 20% = 30000. Only rank=10 (10%) should apply.
        self.assertAlmostEqual(result['player_data'][9010]['tax_isk'], 10_000.0)


class TestVariableTaxMoons(TestCase):
    fixtures = ["moons_sde"]

    def setUp(self):
        corp_info = EveCorporationInfo.objects.create(
            corporation_id=3, corporation_name="Variable Corp",
            corporation_ticker="VAR", member_count=1, ceo_id=1,
        )
        self.corp_audit = CorporationAudit.objects.create(corporation=corp_info)
        self.structure = EveLocation.objects.create(
            location_id=3000000, location_name="Variable Refinery"
        )
        self.char = EveName.objects.create(
            eve_id=9020, name="Variable Miner", category="character"
        )
        self.ore_type = ItemType.objects.get(pk=46295)
        OrePrice.objects.create(item=self.ore_type, price=100, goo_only=False)

        self.tax_rates = OreTaxRates.objects.create(
            tag="variable_test", refine_rate=87.5,
            ore_rate=10, ubiquitous_rate=10, common_rate=10,
            uncommon_rate=10, rare_rate=10, exceptional_rate=10,
        )
        # OreTax price = 15 ISK/unit for this ore under this rate
        OreTax.objects.create(item=self.ore_type, price=15, tax=self.tax_rates)

        MiningTax.objects.create(
            use_variable_tax=True, tax_rate=self.tax_rates, flat_tax_rate=0, rank=1
        )

        self.start = timezone.now() - timedelta(days=30)
        self.end = timezone.now() + timedelta(days=1)

        _make_observation(
            self.corp_audit, self.structure, self.char,
            self.ore_type, quantity=1000, last_updated=timezone.now(),
        )

    def test_variable_tax_uses_ore_tax_price(self):
        result = MiningObservation.tax_moons(self.start, self.end)
        # tax_value = OreTax.price * quantity = 15 * 1000
        self.assertAlmostEqual(result['player_data'][9020]['tax_isk'], 15_000.0)

    def test_variable_tax_isk_value_still_from_ore_price(self):
        result = MiningObservation.tax_moons(self.start, self.end)
        # isk_value = OrePrice.price * quantity = 100 * 1000
        self.assertAlmostEqual(result['player_data'][9020]['totals_isk'], 100_000.0)
