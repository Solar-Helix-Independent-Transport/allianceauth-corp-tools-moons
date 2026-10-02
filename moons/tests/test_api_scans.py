from decimal import Decimal

from eve_sde.models import (
    Constellation, ItemGroup, ItemType, Moon, Region, SolarSystem,
)
from ninja.testing import TestClient

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.tests.auth_utils import AuthUtils

from moons.api import api
from moons.models import MoonRental, MoonScan, OrePrice, OreTax, OreTaxRates

MOON_1 = 40161708
CINNABAR, BITUMENS = 45506, 45492


def _paste(moon_id, ores):
    lines = [f"Moon {moon_id}"]
    for type_id, fraction in ores.items():
        lines.append(f"\tOre\t{fraction}\t{type_id}\t30002542\t40161707\t{moon_id}")
    return "\r\n".join(lines)


def _perm(codename):
    return Permission.objects.get_by_natural_key(codename, "moons", "moonscan")


class TestScanImportApi(TestCase):
    @classmethod
    def setUpTestData(cls):
        region = Region.objects.create(id=10000001, name="Test Region")
        constellation = Constellation.objects.create(id=20000001, name="Test Constellation", region=region)
        system = SolarSystem.objects.create(id=30002542, name="Auga", constellation=constellation)
        cls.moon = Moon.objects.create(id=MOON_1, name="Auga V - Moon 1", solar_system=system)
        rare = ItemGroup.objects.create(id=1922, name="Rare Moon Asteroids")
        ubiq = ItemGroup.objects.create(id=1884, name="Ubiquitous Moon Asteroids")
        ItemType.objects.create(id=CINNABAR, name="Cinnabar", group=rare)
        ItemType.objects.create(id=BITUMENS, name="Bitumens", group=ubiq)

        cls.nobody = AuthUtils.create_user("no_scan_perms")
        cls.changer = AuthUtils.create_user("scan_changer")
        cls.changer.user_permissions.add(_perm("add_moonscan"), _perm("change_moonscan"))

    def setUp(self):
        self.client = TestClient(api)

    def test_import_endpoints_need_add_permission(self):
        body = {"text": _paste(MOON_1, {CINNABAR: "0.5"})}
        for path in ("/scans/preview", "/scans/import"):
            with self.subTest(path):
                response = self.client.post(path, json=body, user=self.nobody)
                self.assertEqual(response.status_code, 403)
        self.assertFalse(MoonScan.objects.exists())

    def test_preview_shows_previous_and_new_fractions_per_ore_without_writing(self):
        scan = MoonScan.objects.create(moon=self.moon, added_at=timezone.now())
        scan.ores.create(ore_id=CINNABAR, fraction=Decimal("0.4"))
        scan.ores.create(ore_id=BITUMENS, fraction=Decimal("0.6"))

        response = self.client.post(
            "/scans/preview", json={"text": _paste(MOON_1, {CINNABAR: "0.5"})}, user=self.changer)

        self.assertEqual(response.status_code, 200)
        [moon] = response.json()
        self.assertEqual(moon["moon_id"], MOON_1)
        self.assertEqual(moon["name"], "Auga V - Moon 1")
        self.assertEqual(moon["status"], "changed")
        self.assertEqual(
            sorted(moon["ores"], key=lambda o: o["type_id"]),
            [
                {"type_id": BITUMENS, "name": "Bitumens", "fraction": None, "previous": 0.6},
                {"type_id": CINNABAR, "name": "Cinnabar", "fraction": 0.5, "previous": 0.4},
            ],
        )
        self.assertEqual(MoonScan.objects.get().ores.count(), 2)

    def test_import_writes_scan_as_requesting_user(self):
        response = self.client.post(
            "/scans/import", json={"text": _paste(MOON_1, {CINNABAR: "0.5"})}, user=self.changer)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([m["status"] for m in response.json()], ["new"])
        self.assertEqual(MoonScan.objects.get(moon_id=MOON_1).added_by, self.changer)

    def test_user_permissions_expose_scan_flags(self):
        viewer = AuthUtils.create_user("scan_viewer")
        viewer.user_permissions.add(_perm("view_moonscan"))

        for user, expected in (
            (self.nobody, (False, False, False)),
            (self.changer, (True, True, False)),
            (viewer, (False, False, True)),
        ):
            with self.subTest(user.username):
                data = self.client.get("/user/permissions", user=user).json()
                self.assertEqual(
                    (data["import_scans"], data["change_scans"], data["view_scans"]), expected)


def _profile(tag, flagged):
    return OreTaxRates.objects.create(
        tag=tag, refine_rate=Decimal("100"), ore_rate=0, ubiquitous_rate=0, common_rate=0,
        uncommon_rate=0, rare_rate=10, exceptional_rate=0, show_in_moon_values=flagged)


class TestMoonValuesApi(TestCase):
    @classmethod
    def setUpTestData(cls):
        region = Region.objects.create(id=10000001, name="Test Region")
        constellation = Constellation.objects.create(id=20000001, name="Test Constellation", region=region)
        system = SolarSystem.objects.create(id=30002542, name="Auga", constellation=constellation)
        moon = Moon.objects.create(id=MOON_1, name="Auga V - Moon 1", solar_system=system)
        rare = ItemGroup.objects.create(id=1922, name="Rare Moon Asteroids")
        cinnabar = ItemType.objects.create(id=CINNABAR, name="Cinnabar", group=rare)

        cls.viewer = AuthUtils.create_user("scan_viewer")
        cls.viewer.user_permissions.add(_perm("view_moonscan"))
        AuthUtils.add_main_character_2(cls.viewer, "Scout Main", 2112000001, corp_id=2112000002, corp_name="Scouts")
        cls.nobody = AuthUtils.create_user("no_scan_perms")

        cls.flagged = _profile("Rental", True)
        cls.hidden = _profile("Internal", False)
        OrePrice.objects.create(item=cinnabar, price=Decimal("1000"))
        OreTax.objects.create(item=cinnabar, tax=cls.flagged, price=Decimal("100"))

        scan = MoonScan.objects.create(moon=moon, added_by=cls.viewer, added_at=timezone.now())
        scan.ores.create(ore=cinnabar, fraction=Decimal("0.5"))

    def setUp(self):
        self.client = TestClient(api)

    def test_value_endpoints_need_view_permission(self):
        for path in ("/scans/profiles", f"/scans/values?tax_rate={self.flagged.id}"):
            with self.subTest(path):
                self.assertEqual(self.client.get(path, user=self.nobody).status_code, 403)

    def test_profiles_lists_only_flagged_tax_profiles(self):
        response = self.client.get("/scans/profiles", user=self.viewer)

        self.assertEqual(response.json(), [{"id": self.flagged.id, "tag": "Rental"}])

    def test_values_for_a_flagged_profile(self):
        response = self.client.get(f"/scans/values?tax_rate={self.flagged.id}", user=self.viewer)

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json()["prices_updated"])
        [moon] = response.json()["moons"]
        # 1,440,000 units at 1000 (100% refine), tax 100 per unit
        self.assertEqual((moon["moon"]["id"], moon["moon"]["name"]), (MOON_1, "Auga V - Moon 1"))
        self.assertEqual(moon["system"], "Auga")
        self.assertEqual(moon["region"], "Test Region")
        self.assertEqual(moon["value"], 1440000000)
        self.assertEqual(moon["tax"], 144000000)
        self.assertEqual(moon["total_fraction"], 0.5)
        self.assertEqual(moon["ores"], [{"type_id": CINNABAR, "name": "Cinnabar", "fraction": 0.5}])
        self.assertEqual(moon["unpriced"], [])
        self.assertEqual(moon["added_by"], "Scout Main")

    def test_values_for_unflagged_profile_is_not_found(self):
        response = self.client.get(f"/scans/values?tax_rate={self.hidden.id}", user=self.viewer)

        self.assertEqual(response.status_code, 404)


class TestRentalSuggestionApi(TestCase):
    @classmethod
    def setUpTestData(cls):
        region = Region.objects.create(id=10000001, name="Test Region")
        constellation = Constellation.objects.create(id=20000001, name="Test Constellation", region=region)
        system = SolarSystem.objects.create(id=30002542, name="Auga", constellation=constellation)
        cls.moon = Moon.objects.create(id=MOON_1, name="Auga V - Moon 1", solar_system=system)
        cls.unscanned = Moon.objects.create(id=40161709, name="Auga V - Moon 2", solar_system=system)
        rare = ItemGroup.objects.create(id=1922, name="Rare Moon Asteroids")
        cinnabar = ItemType.objects.create(id=CINNABAR, name="Cinnabar", group=rare)

        cls.flagged = _profile("Rental", True)
        cls.hidden = _profile("Internal", False)
        OrePrice.objects.create(item=cinnabar, price=Decimal("1000"))
        OreTax.objects.create(item=cinnabar, tax=cls.flagged, price=Decimal("100.4"))
        scan = MoonScan.objects.create(moon=cls.moon, added_at=timezone.now())
        scan.ores.create(ore=cinnabar, fraction=Decimal("0.5"))

        cls.renter = AuthUtils.create_user("rental_admin")
        cls.renter.user_permissions.add(
            Permission.objects.get_by_natural_key("add_moonrental", "moons", "moonrental"))
        cls.nobody = AuthUtils.create_user("no_rental_perms")

    def setUp(self):
        self.client = TestClient(api)

    def _suggest(self, moon, profile, user):
        return self.client.get(f"/scans/suggestion?moon_id={moon.id}&tax_rate={profile.id}", user=user)

    def test_suggestion_needs_rental_permission(self):
        self.assertEqual(self._suggest(self.moon, self.flagged, self.nobody).status_code, 403)

    def test_suggestion_is_30_day_tax_rounded_to_a_million(self):
        response = self._suggest(self.moon, self.flagged, self.renter)

        # 1,440,000 units * 100.4 = 144,576,000
        self.assertEqual(response.json(), {"price": 145000000})

    def test_unscanned_moon_has_no_suggestion(self):
        self.assertEqual(self._suggest(self.unscanned, self.flagged, self.renter).json(), {"price": None})

    def test_unflagged_profile_is_not_found(self):
        self.assertEqual(self._suggest(self.moon, self.hidden, self.renter).status_code, 404)

    def test_new_rental_stores_note(self):
        char = EveCharacter.objects.create(
            character_id=2112000001, character_name="Renter", corporation_id=2112000002,
            corporation_name="Renters", corporation_ticker="RENT")
        corp = EveCorporationInfo.objects.create(
            corporation_id=2112000002, corporation_name="Renters", corporation_ticker="RENT",
            member_count=1)

        response = self.client.post("/rental/new", data={
            "moon_id": MOON_1, "contact_id": char.character_id,
            "corporation_id": corp.corporation_id, "price": 145000000, "note": "Paid via contract",
        }, user=self.renter)

        self.assertEqual(response.status_code, 200)
        rental = MoonRental.objects.get(moon_id=MOON_1)
        self.assertEqual(rental.note, "Paid via contract")
        self.assertEqual(rental.price, 145000000)

    def test_user_permissions_expose_add_rentals(self):
        self.assertTrue(self.client.get("/user/permissions", user=self.renter).json()["add_rentals"])
        self.assertFalse(self.client.get("/user/permissions", user=self.nobody).json()["add_rentals"])

    def test_rental_admin_without_scan_view_can_list_profiles(self):
        response = self.client.get("/scans/profiles", user=self.renter)

        self.assertEqual(response.json(), [{"id": self.flagged.id, "tag": "Rental"}])
