from decimal import Decimal
from unittest import mock

from eve_sde.models import (
    Constellation, ItemGroup, ItemType, Moon, Region, SolarSystem,
)
from ninja.testing import TestClient

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.tests.auth_utils import AuthUtils

from moons.api import api
from moons.models import MoonRental, MoonScan, OrePrice, OreTax, OreTaxRates
from moons.rent import FuelPricesUnavailable

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
        moon = cls.moon = Moon.objects.create(id=MOON_1, name="Auga V - Moon 1", solar_system=system)
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
        for path in ("/scans/profiles", "/scans/regions", f"/scans/values?tax_rate={self.flagged.id}&region_id=10000001"):
            with self.subTest(path):
                self.assertEqual(self.client.get(path, user=self.nobody).status_code, 403)

    def test_profiles_lists_only_flagged_tax_profiles(self):
        response = self.client.get("/scans/profiles", user=self.viewer)

        self.assertEqual(response.json(), [{
            "id": self.flagged.id, "tag": "Rental", "rent_subtract_metenox_fuel": False,
            "rent_profit_share": 100.0, "rent_minimum": 0,
        }])

    def test_values_for_a_flagged_profile(self):
        response = self.client.get(f"/scans/values?tax_rate={self.flagged.id}&region_id=10000001", user=self.viewer)

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json()["prices_updated"])
        [moon] = response.json()["moons"]
        # 1,440,000 units at 1000 (100% refine), tax 100 per unit
        self.assertEqual((moon["moon"]["id"], moon["moon"]["name"]), (MOON_1, "Auga V - Moon 1"))
        self.assertEqual(moon["system"], "Auga")
        self.assertEqual(moon["region"], "Test Region")
        self.assertEqual(moon["value"], 1440000000)
        self.assertEqual(moon["tax"], 144000000)
        self.assertEqual(moon["rent"], 144000000)  # no rent options: tax rounded to a million
        self.assertIsNone(response.json()["fuel_30d"])
        self.assertEqual(moon["total_fraction"], 0.5)
        self.assertEqual(moon["ores"], [{"type_id": CINNABAR, "name": "Cinnabar", "fraction": 0.5}])
        self.assertEqual(moon["unpriced"], [])
        self.assertEqual(moon["added_by"], "Scout Main")
        self.assertEqual(moon["rarity"], 32)
        self.assertEqual((moon["rented"], moon["rented_by"], moon["rental_price"]), (False, None, None))

    def _rent(self, end_date=None):
        char = EveCharacter.objects.create(
            character_id=2112000011, character_name="Renter", corporation_id=2112000012,
            corporation_name="Renters", corporation_ticker="RENT")
        corp = EveCorporationInfo.objects.create(
            corporation_id=2112000012, corporation_name="Renters", corporation_ticker="RENT",
            member_count=1)
        MoonRental.objects.create(moon=self.moon, contact=char, corporation=corp, price=250_000_000,
                                  start_date=timezone.now(), end_date=end_date)

    def _values_moon(self, user):
        return self.client.get(
            f"/scans/values?tax_rate={self.flagged.id}&region_id=10000001", user=user).json()["moons"][0]

    def test_rented_moon_shows_rented_without_who_or_price(self):
        self._rent()

        moon = self._values_moon(self.viewer)

        self.assertEqual((moon["rented"], moon["rented_by"], moon["rental_price"]), (True, None, None))

    def test_rented_moon_shows_who_and_price_with_rental_view_permission(self):
        self._rent()
        self.viewer.user_permissions.add(
            Permission.objects.get_by_natural_key("view_moonrental", "moons", "moonrental"))

        moon = self._values_moon(User.objects.get(pk=self.viewer.pk))  # fresh permission cache

        self.assertEqual((moon["rented"], moon["rented_by"], moon["rental_price"]),
                         (True, "Renter", 250_000_000))

    def test_ended_rental_is_available(self):
        self._rent(end_date=timezone.now())

        self.assertFalse(self._values_moon(self.viewer)["rented"])

    def test_scanned_regions_with_moon_counts(self):
        response = self.client.get("/scans/regions", user=self.viewer)

        self.assertEqual(response.json(), [{"id": 10000001, "name": "Test Region", "moons": 1}])

    def test_values_only_for_the_requested_region(self):
        other = Region.objects.create(id=10000002, name="Other Region")
        constellation = Constellation.objects.create(id=20000002, name="Other Constellation", region=other)
        system = SolarSystem.objects.create(id=30000002, name="Elsewhere", constellation=constellation)
        far = Moon.objects.create(id=40000099, name="Elsewhere I - Moon 1", solar_system=system)
        MoonScan.objects.create(moon=far, added_at=timezone.now()).ores.create(
            ore_id=CINNABAR, fraction=Decimal("0.1"))

        response = self.client.get(
            f"/scans/values?tax_rate={self.flagged.id}&region_id=10000002", user=self.viewer)

        self.assertEqual([m["moon"]["id"] for m in response.json()["moons"]], [40000099])

    def test_values_rent_follows_the_profile_rent_options(self):
        self.flagged.rent_subtract_metenox_fuel = True
        self.flagged.rent_profit_share = 50
        self.flagged.save()
        with mock.patch("moons.rent.cached_fuel_prices", return_value=(1000, {"A": 10000})):
            response = self.client.get(
                f"/scans/values?tax_rate={self.flagged.id}&region_id=10000001", user=self.viewer)

        # fuel: 1,000 x 720 x 200 + 10,000 x 720 x 5 = 180,000,000
        # (144,000,000 - 180,000,000) x 50% rounds to -18m, floored at the 0 minimum
        self.assertEqual(response.json()["fuel_30d"], 180000000)
        self.assertEqual(response.json()["moons"][0]["rent"], 0)

    def test_values_without_fuel_prices_is_unavailable(self):
        self.flagged.rent_subtract_metenox_fuel = True
        self.flagged.save()
        with mock.patch("moons.rent.cached_fuel_prices", side_effect=FuelPricesUnavailable("No fuel")):
            response = self.client.get(
                f"/scans/values?tax_rate={self.flagged.id}&region_id=10000001", user=self.viewer)

        self.assertEqual(response.status_code, 503)

    def test_values_for_unflagged_profile_is_not_found(self):
        response = self.client.get(f"/scans/values?tax_rate={self.hidden.id}&region_id=10000001", user=self.viewer)

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

    def test_suggestion_is_the_suggested_rent_of_the_profile(self):
        self.flagged.rent_profit_share = 50
        self.flagged.rent_minimum = 100_000_000
        self.flagged.save()

        response = self._suggest(self.moon, self.flagged, self.renter)

        # 144,576,000 x 50% = 72,288,000 -> 72m, raised to the 100m minimum
        self.assertEqual(response.json(), {"price": 100000000})

    def test_suggestion_without_fuel_prices_is_unavailable(self):
        self.flagged.rent_subtract_metenox_fuel = True
        self.flagged.save()
        with mock.patch("moons.rent.cached_fuel_prices", side_effect=FuelPricesUnavailable("No fuel")):
            response = self._suggest(self.moon, self.flagged, self.renter)

        self.assertEqual(response.status_code, 503)

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

        self.assertEqual(response.json(), [{
            "id": self.flagged.id, "tag": "Rental", "rent_subtract_metenox_fuel": False,
            "rent_profit_share": 100.0, "rent_minimum": 0,
        }])


class _ActiveRentalApiTestCase(TestCase):
    """One active rental, a user who can change rentals and one who can only add them."""

    @classmethod
    def setUpTestData(cls):
        region = Region.objects.create(id=10000001, name="Test Region")
        constellation = Constellation.objects.create(id=20000001, name="Test Constellation", region=region)
        system = SolarSystem.objects.create(id=30002542, name="Auga", constellation=constellation)
        moon = Moon.objects.create(id=MOON_1, name="Auga V - Moon 1", solar_system=system)
        char = EveCharacter.objects.create(
            character_id=2112000001, character_name="Renter", corporation_id=2112000002,
            corporation_name="Renters", corporation_ticker="RENT")
        corp = EveCorporationInfo.objects.create(
            corporation_id=2112000002, corporation_name="Renters", corporation_ticker="RENT",
            member_count=1)
        cls.rental = MoonRental.objects.create(
            moon=moon, contact=char, corporation=corp, price=100_000_000,
            start_date=timezone.now(), note="rented by someone")

        cls.editor = AuthUtils.create_user("rental_editor")
        cls.editor.user_permissions.add(
            Permission.objects.get_by_natural_key("change_moonrental", "moons", "moonrental"))
        AuthUtils.add_main_character_2(cls.editor, "Editor Main", 2112000003, corp_id=2112000002, corp_name="Renters")
        cls.adder = AuthUtils.create_user("rental_adder")
        cls.adder.user_permissions.add(
            Permission.objects.get_by_natural_key("add_moonrental", "moons", "moonrental"))

    def setUp(self):
        self.client = TestClient(api)



class TestEndRentalApi(_ActiveRentalApiTestCase):
    def _end(self, user, note, rental_id=None):
        return self.client.post(f"/rental/{rental_id or self.rental.id}/end", data={"note": note}, user=user)

    def test_unrent_ends_rental_and_appends_note_with_who_did_it(self):
        response = self._end(self.editor, "Stopped paying")

        self.assertEqual(response.status_code, 200)
        self.rental.refresh_from_db()
        self.assertIsNotNone(self.rental.end_date)
        self.assertEqual(self.rental.note, "rented by someone\nUnrented, completed by Editor Main: Stopped paying")

    def test_unrent_needs_change_permission(self):
        self.assertEqual(self._end(self.adder, "Stopped paying").status_code, 403)
        self.rental.refresh_from_db()
        self.assertIsNone(self.rental.end_date)

    def test_unrent_needs_a_note(self):
        self.assertEqual(self._end(self.editor, "   ").status_code, 400)
        self.rental.refresh_from_db()
        self.assertIsNone(self.rental.end_date)

    def test_unrent_of_an_ended_rental_is_not_found(self):
        self._end(self.editor, "Stopped paying")

        self.assertEqual(self._end(self.editor, "Again").status_code, 404)

    def test_rental_list_carries_the_rental_id_and_note(self):
        rentals = self.client.get("/rental/list", user=self.adder).json()

        self.assertEqual([(r["id"], r["note"]) for r in rentals], [(self.rental.id, "rented by someone")])


class TestScanCoverageApi(TestCase):
    @classmethod
    def setUpTestData(cls):
        region = Region.objects.create(id=10000001, name="Test Region")
        constellation = Constellation.objects.create(id=20000001, name="Test Constellation", region=region)
        auga = SolarSystem.objects.create(id=30002542, name="Auga", constellation=constellation)
        bodgal = SolarSystem.objects.create(id=30002543, name="Bodgal", constellation=constellation)
        scanned = Moon.objects.create(id=MOON_1, name="Auga V - Moon 1", solar_system=auga)
        Moon.objects.create(id=40161709, name="Auga V - Moon 2", solar_system=auga)
        Moon.objects.create(id=40161800, name="Bodgal I - Moon 1", solar_system=bodgal)
        empty = Region.objects.create(id=10000002, name="Unscanned Region")
        far = SolarSystem.objects.create(
            id=30000002, name="Elsewhere",
            constellation=Constellation.objects.create(id=20000002, name="Far", region=empty))
        Moon.objects.create(id=40000099, name="Elsewhere I - Moon 1", solar_system=far)
        MoonScan.objects.create(moon=scanned, added_at=timezone.now())

        cls.importer = AuthUtils.create_user("scan_importer")
        cls.importer.user_permissions.add(_perm("add_moonscan"))
        cls.viewer = AuthUtils.create_user("scan_viewer")
        cls.viewer.user_permissions.add(_perm("view_moonscan"))
        cls.nobody = AuthUtils.create_user("no_scan_perms")

    def setUp(self):
        self.client = TestClient(api)

    def test_coverage_needs_import_or_view_permission(self):
        for path in ("/scans/coverage", "/scans/coverage/10000001"):
            self.assertEqual(self.client.get(path, user=self.nobody).status_code, 403)
            self.assertEqual(self.client.get(path, user=self.viewer).status_code, 200)

    def test_coverage_counts_every_region_with_moons_including_unscanned(self):
        response = self.client.get("/scans/coverage", user=self.importer)

        self.assertEqual(response.json(), [
            {"id": 10000001, "name": "Test Region", "moons": 3, "scanned": 1},
            {"id": 10000002, "name": "Unscanned Region", "moons": 1, "scanned": 0},
        ])

    def test_missing_moons_by_constellation_and_system(self):
        response = self.client.get("/scans/coverage/10000001", user=self.importer)

        self.assertEqual(response.json(), [
            {"id": 40161709, "name": "Auga V - Moon 2", "system": "Auga", "constellation": "Test Constellation"},
            {"id": 40161800, "name": "Bodgal I - Moon 1", "system": "Bodgal", "constellation": "Test Constellation"},
        ])


class TestRepriceMethodApi(_ActiveRentalApiTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile = _profile("Rental", True)

    def _set(self, user, method_id=None):
        data = {"reprice_method_id": method_id} if method_id else {}
        return self.client.post(f"/rental/{self.rental.id}/reprice_method", data=data, user=user)

    def test_set_and_clear_reprice_method(self):
        self.assertEqual(self._set(self.editor, self.profile.id).status_code, 200)
        self.rental.refresh_from_db()
        self.assertEqual(self.rental.reprice_method, self.profile)

        self.assertEqual(self._set(self.editor).status_code, 200)
        self.rental.refresh_from_db()
        self.assertIsNone(self.rental.reprice_method)

    def test_setting_reprice_method_needs_change_permission(self):
        self.assertEqual(self._set(self.adder, self.profile.id).status_code, 403)

    def test_unknown_reprice_method_is_rejected(self):
        self.assertEqual(self._set(self.editor, 999999).status_code, 400)

    def test_rental_list_shows_reprice_method(self):
        self.rental.reprice_method = self.profile
        self.rental.save()

        [rental] = self.client.get("/rental/list", user=self.adder).json()

        self.assertEqual(rental["reprice_method"], {"id": self.profile.id, "tag": "Rental"})

    def test_new_rental_with_reprice_method(self):
        self.rental.end_date = timezone.now()
        self.rental.save()

        response = self.client.post("/rental/new", data={
            "moon_id": MOON_1, "contact_id": 2112000001, "corporation_id": 2112000002,
            "price": 100000000, "reprice_method_id": self.profile.id,
        }, user=self.adder)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reprice_method"], {"id": self.profile.id, "tag": "Rental"})
