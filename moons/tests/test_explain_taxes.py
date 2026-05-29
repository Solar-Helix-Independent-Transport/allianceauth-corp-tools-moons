from datetime import timedelta

from corptools.models import CorporationAudit, EveLocation, EveName
from eve_sde.models import Constellation, ItemType, Moon, Region, SolarSystem

from django.test import TestCase
from django.utils import timezone

from allianceauth.eveonline.models import EveCorporationInfo

from moons.models import MiningObservation, MiningTax, OrePrice, OreTaxRates


def _make_geo_chain(suffix=""):
    region = Region.objects.create(id=10000100 + hash(suffix) % 1000, name=f"Region{suffix}")
    constellation = Constellation.objects.create(
        id=20000100 + hash(suffix) % 1000, name=f"Constellation{suffix}", region=region
    )
    system = SolarSystem.objects.create(
        id=30000100 + hash(suffix) % 1000, name=f"System{suffix}", constellation=constellation
    )
    moon = Moon.objects.create(id=40000100 + hash(suffix) % 1000, name=f"Moon{suffix}", solar_system=system)
    return region, constellation, system, moon


def _make_observation(corp_audit, structure, char_name, ore_type, last_updated):
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
        quantity=100,
        recorded_corporation_id=corp_audit.corporation.corporation_id,
        type_name=ore_type,
        type_id=ore_type.pk,
    )


class TestExplainTaxes(TestCase):
    fixtures = ["moons_sde"]

    def setUp(self):
        corp_info = EveCorporationInfo.objects.create(
            corporation_id=1, corporation_name="Explain Corp",
            corporation_ticker="EXP", member_count=1, ceo_id=1,
        )
        self.corp_audit = CorporationAudit.objects.create(corporation=corp_info)
        self.structure = EveLocation.objects.create(location_id=7000001, location_name="Explain Refinery")
        self.char = EveName.objects.create(eve_id=7001, name="Explain Miner", category="character")
        self.ore_type = ItemType.objects.get(pk=46295)
        OrePrice.objects.create(item=self.ore_type, price=100, goo_only=False)

        self.start = timezone.now() - timedelta(days=30)
        self.end = timezone.now() + timedelta(days=1)

    def test_no_taxes_returns_empty(self):
        result = MiningObservation.explain_taxes(self.start, self.end)
        self.assertEqual(result['structures'], [])
        self.assertEqual(result['taxes'], [])

    def test_structure_appears_in_correct_tax(self):
        MiningTax.objects.create(use_variable_tax=False, flat_tax_rate=0.10, rank=1)
        _make_observation(self.corp_audit, self.structure, self.char, self.ore_type, timezone.now())
        result = MiningObservation.explain_taxes(self.start, self.end)
        self.assertIn("Explain Refinery", result['structures'])
        self.assertEqual(len(result['taxes']), 1)
        self.assertIn("Explain Refinery", result['taxes'][0]['structures'])

    def test_rank_deduplication_in_explain(self):
        MiningTax.objects.create(use_variable_tax=False, flat_tax_rate=0.10, rank=10)
        MiningTax.objects.create(use_variable_tax=False, flat_tax_rate=0.20, rank=5)
        _make_observation(self.corp_audit, self.structure, self.char, self.ore_type, timezone.now())
        result = MiningObservation.explain_taxes(self.start, self.end)
        # Structure should appear in exactly one tax group (the highest rank)
        all_tax_structures = [s for t in result['taxes'] for s in t['structures']]
        self.assertEqual(all_tax_structures.count("Explain Refinery"), 1)
        # It should be in the rank=10 tax (first in the list since ordered by -rank)
        self.assertIn("Explain Refinery", result['taxes'][0]['structures'])
        self.assertNotIn("Explain Refinery", result['taxes'][1]['structures'])

    def test_observation_outside_window_not_included(self):
        MiningTax.objects.create(use_variable_tax=False, flat_tax_rate=0.10, rank=1)
        old_date = timezone.now() - timedelta(days=60)
        _make_observation(self.corp_audit, self.structure, self.char, self.ore_type, old_date)
        window_start = timezone.now() - timedelta(days=7)
        result = MiningObservation.explain_taxes(window_start, self.end)
        self.assertEqual(result['structures'], [])

    def test_two_structures_in_same_tax(self):
        MiningTax.objects.create(use_variable_tax=False, flat_tax_rate=0.10, rank=1)
        structure2 = EveLocation.objects.create(location_id=7000002, location_name="Second Refinery")
        char2 = EveName.objects.create(eve_id=7002, name="Second Miner", category="character")
        _make_observation(self.corp_audit, self.structure, self.char, self.ore_type, timezone.now())
        _make_observation(self.corp_audit, structure2, char2, self.ore_type, timezone.now())
        result = MiningObservation.explain_taxes(self.start, self.end)
        self.assertIn("Explain Refinery", result['taxes'][0]['structures'])
        self.assertIn("Second Refinery", result['taxes'][0]['structures'])


class TestMiningTaxStr(TestCase):
    def _make_rates(self):
        return OreTaxRates.objects.create(
            tag="Standard", refine_rate=87.5,
            ore_rate=5, ubiquitous_rate=5, common_rate=5,
            uncommon_rate=5, rare_rate=5, exceptional_rate=5,
        )

    def test_flat_rate_everywhere_everyone(self):
        tax = MiningTax.objects.create(use_variable_tax=False, flat_tax_rate=0.10, rank=1)
        result = str(tax)
        self.assertIn("Rank 1", result)
        self.assertIn("Everyone", result)
        self.assertIn("Everywhere", result)
        self.assertIn("10.0%", result)

    def test_variable_rate_shows_tag(self):
        rates = self._make_rates()
        tax = MiningTax.objects.create(use_variable_tax=True, tax_rate=rates, flat_tax_rate=0, rank=2)
        result = str(tax)
        self.assertIn("Variable", result)
        self.assertIn("Standard", result)

    def test_corp_filter_shows_corp_name(self):
        corp = EveCorporationInfo.objects.create(
            corporation_id=100, corporation_name="Mining Inc",
            corporation_ticker="MNG", member_count=1, ceo_id=1,
        )
        tax = MiningTax.objects.create(use_variable_tax=False, flat_tax_rate=0.05, rank=1, corp=corp)
        result = str(tax)
        self.assertIn("Mining Inc", result)

    def test_region_filter_shows_region_name(self):
        region = Region.objects.create(id=10000200, name="The Forge")
        tax = MiningTax.objects.create(use_variable_tax=False, flat_tax_rate=0.05, rank=1, region=region)
        result = str(tax)
        self.assertIn("Region", result)
        self.assertIn("The Forge", result)

    def test_constellation_filter(self):
        region = Region.objects.create(id=10000201, name="Test Region")
        const = Constellation.objects.create(id=20000201, name="Kimotoro", region=region)
        tax = MiningTax.objects.create(use_variable_tax=False, flat_tax_rate=0.05, rank=1, constellation=const)
        result = str(tax)
        self.assertIn("Constellation", result)
        self.assertIn("Kimotoro", result)

    def test_system_filter(self):
        region = Region.objects.create(id=10000202, name="Test Region2")
        const = Constellation.objects.create(id=20000202, name="Test Const2", region=region)
        system = SolarSystem.objects.create(id=30000202, name="Jita", constellation=const)
        tax = MiningTax.objects.create(use_variable_tax=False, flat_tax_rate=0.05, rank=1, system=system)
        result = str(tax)
        self.assertIn("System", result)
        self.assertIn("Jita", result)

    def test_moon_filter(self):
        region = Region.objects.create(id=10000203, name="Test Region3")
        const = Constellation.objects.create(id=20000203, name="Test Const3", region=region)
        system = SolarSystem.objects.create(id=30000203, name="Test System3", constellation=const)
        moon = Moon.objects.create(id=40000203, name="Jita IV - Moon 4", solar_system=system)
        tax = MiningTax.objects.create(use_variable_tax=False, flat_tax_rate=0.05, rank=1, moon=moon)
        result = str(tax)
        self.assertIn("Jita IV - Moon 4", result)

    def test_region_takes_priority_over_constellation(self):
        region = Region.objects.create(id=10000204, name="Priority Region")
        const = Constellation.objects.create(id=20000204, name="Priority Const", region=region)
        tax = MiningTax.objects.create(
            use_variable_tax=False, flat_tax_rate=0.05, rank=1,
            region=region, constellation=const,
        )
        result = str(tax)
        self.assertIn("Region:", result)
        self.assertNotIn("Constellation:", result)

    def test_everyone_when_no_corp(self):
        tax = MiningTax.objects.create(use_variable_tax=False, flat_tax_rate=0.10, rank=1)
        self.assertIn("Everyone", str(tax))
