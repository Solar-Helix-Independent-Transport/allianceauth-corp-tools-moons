from decimal import Decimal
from unittest import mock

from eve_sde.models import (
    Constellation, ItemGroup, ItemType, Moon, Region, SolarSystem,
)

from django.test import TestCase
from django.utils import timezone

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.tests.auth_utils import AuthUtils

from moons import repricing
from moons.models import (
    MoonRental, MoonScan, OrePrice, OreTax, OreTaxRates, RentalRepricing,
)
from moons.tasks import reprice_rentals

CINNABAR = 45506


class TestRepricing(TestCase):
    """Each scanned moon is 50% Cinnabar: 1,440,000 units at 100 tax = 144,000,000 a month."""

    @classmethod
    def setUpTestData(cls):
        region = Region.objects.create(id=10000001, name="Test Region")
        constellation = Constellation.objects.create(id=20000001, name="Test Constellation", region=region)
        system = SolarSystem.objects.create(id=30002542, name="Auga", constellation=constellation)
        other = Region.objects.create(id=10000002, name="Other Region")
        far = SolarSystem.objects.create(
            id=30000002, name="Elsewhere",
            constellation=Constellation.objects.create(id=20000002, name="Far", region=other))
        cinnabar = ItemType.objects.create(
            id=CINNABAR, name="Cinnabar", group=ItemGroup.objects.create(id=1922, name="Rare Moon Asteroids"))
        cls.profile = OreTaxRates.objects.create(
            tag="Rental", refine_rate=Decimal("100"), ore_rate=0, ubiquitous_rate=0, common_rate=0,
            uncommon_rate=0, rare_rate=10, exceptional_rate=0, rent_profit_share=50, rent_minimum=50_000_000)
        OrePrice.objects.create(item=cinnabar, price=Decimal("1000"))
        OreTax.objects.create(item=cinnabar, tax=cls.profile, price=Decimal("100"))
        # a whole-price profile: 144,000,000 a month at 100% share
        cls.metenox = OreTaxRates.objects.create(
            tag="Metenox", refine_rate=Decimal("100"), ore_rate=0, ubiquitous_rate=0, common_rate=0,
            uncommon_rate=0, rare_rate=10, exceptional_rate=0)
        OreTax.objects.create(item=cinnabar, tax=cls.metenox, price=Decimal("100"))

        cls.renters = EveCorporationInfo.objects.create(
            corporation_id=2112000002, corporation_name="Renters", corporation_ticker="RENT", member_count=1)
        cls.user = AuthUtils.create_user("renter")
        owned = EveCharacter.objects.create(
            character_id=2112000001, character_name="Renter", corporation_id=2112000002,
            corporation_name="Renters", corporation_ticker="RENT")
        CharacterOwnership.objects.create(user=cls.user, character=owned, owner_hash="hash")
        unowned = EveCharacter.objects.create(
            character_id=2112000009, character_name="Stranger", corporation_id=2112000002,
            corporation_name="Renters", corporation_ticker="RENT")

        def moon(moon_id, name, scanned=True, solar_system=system):
            m = Moon.objects.create(id=moon_id, name=name, solar_system=solar_system)
            if scanned:
                MoonScan.objects.create(moon=m, added_at=timezone.now()).ores.create(
                    ore=cinnabar, fraction=Decimal("0.5"))
            return m

        def rental(m, contact=owned, price=100_000_000, method=cls.profile):
            return MoonRental.objects.create(
                moon=m, contact=contact, corporation=cls.renters, price=price,
                start_date=timezone.now(), note="rented", reprice_method=method)

        cls.repriced = rental(moon(40000001, "Auga I - Moon 1"))
        cls.unknown_owner = rental(moon(40000002, "Auga I - Moon 2"), contact=unowned)
        cls.no_scan = rental(moon(40000003, "Auga I - Moon 3", scanned=False))
        cls.no_method = rental(moon(40000004, "Auga I - Moon 4"), method=None)
        cls.other_method = rental(moon(40000005, "Elsewhere I - Moon 1", solar_system=far), method=cls.metenox)
        cls.free = rental(moon(40000006, "Auga I - Moon 6"), price=0)
        cls.ended = rental(moon(40000007, "Auga I - Moon 7"))
        cls.ended.end_date = timezone.now()
        cls.ended.save()

        cls.settings = RentalRepricing.objects.create(channel_id=123)

    def _prices(self):
        return {r.pk: r.price for r in MoonRental.objects.all()}

    def test_reprices_covered_rentals_and_notes_the_change(self):
        result = repricing.reprice(self.settings)

        # Rental: 144,000,000 x 50% = 72,000,000; Metenox: all 144,000,000
        self.assertEqual([(c.rental.pk, c.old, c.new) for c in result.changes],
                         [(self.repriced.pk, 100_000_000, 72_000_000),
                          (self.other_method.pk, 100_000_000, 144_000_000)])
        self.repriced.refresh_from_db()
        self.assertEqual(self.repriced.price, 72_000_000)
        self.assertRegex(self.repriced.note, r"^rented\n\d{4}/\d\d/\d\d - Old: 100,000,000 - New: 72,000,000$")

    def test_leaves_rentals_without_a_reprice_method_and_ended_or_free_rentals_alone(self):
        repricing.reprice(self.settings)

        for rental in (self.no_method, self.free, self.ended, self.unknown_owner, self.no_scan):
            before = rental.price
            rental.refresh_from_db()
            self.assertEqual((rental.price, rental.note), (before, "rented"))

    def test_lists_rentals_it_cannot_price(self):
        result = repricing.reprice(self.settings)

        self.assertEqual(result.skipped, [
            "Auga I - Moon 2 (Unknown Owner: Stranger)",
            "Auga I - Moon 3 (Renter) (No Moon Scan)",
        ])

    def test_dry_run_changes_nothing(self):
        self.settings.dry_run = True
        before = self._prices()

        result = repricing.reprice(self.settings)

        self.assertEqual(result.changes[0].new, 72_000_000)
        self.assertEqual(self._prices(), before)
        self.assertEqual(result.title, "Projected Metenox Rental Prices")

    def test_task_messages_renters_and_posts_summary(self):
        with mock.patch("moons.tasks.app_settings.discord_bot_active", return_value=True), \
                mock.patch("moons.tasks._send_pages") as send:
            reprice_rentals()

        targets = [c.kwargs for c in send.call_args_list]
        self.assertEqual(targets, [{"user_pk": self.user.pk}, {"channel_id": 123}])
        dm, summary = (c.args[0] for c in send.call_args_list)
        self.assertIn("Auga I - Moon 1", "\n".join(dm))
        self.assertIn("Reprice methods: Metenox (1), Rental (1)", summary)
        self.assertIn("Total moons updated: 2", summary)
        self.settings.refresh_from_db()
        self.assertIsNotNone(self.settings.last_run)

    def test_task_dry_run_posts_summary_only(self):
        self.settings.dry_run = True
        self.settings.save()
        with mock.patch("moons.tasks.app_settings.discord_bot_active", return_value=True), \
                mock.patch("moons.tasks._send_pages") as send:
            reprice_rentals()

        self.assertEqual([c.kwargs for c in send.call_args_list], [{"channel_id": 123}])

    def test_task_makes_default_settings_when_none_exist(self):
        RentalRepricing.objects.all().delete()

        reprice_rentals()

        self.assertEqual(RentalRepricing.objects.count(), 1)
        self.repriced.refresh_from_db()
        self.assertEqual(self.repriced.price, 72_000_000)
