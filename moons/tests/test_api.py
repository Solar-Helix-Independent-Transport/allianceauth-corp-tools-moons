from datetime import timedelta

from corptools.models import CorporationAudit, EveLocation
from eve_sde.models import Constellation, Moon, Region, SolarSystem
from ninja.testing import TestClient

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.tests.auth_utils import AuthUtils

from moons.api import api
from moons.models import MoonFrack, MoonRental


def _build_geo_chain():
    region = Region.objects.create(id=10000001, name="Test Region")
    constellation = Constellation.objects.create(id=20000001, name="Test Constellation", region=region)
    system = SolarSystem.objects.create(id=30000001, name="Test System", constellation=constellation)
    moon = Moon.objects.create(id=40000001, name="Test Moon I", solar_system=system)
    return region, constellation, system, moon


class TestUserPermissionsEndpoint(TestCase):
    def setUp(self):
        self.client = TestClient(api)
        self.user = AuthUtils.create_user("perm_test_user")

    def test_unauthenticated_returns_401(self):
        response = self.client.get("/user/permissions")
        self.assertEqual(response.status_code, 401)

    def test_authenticated_no_perms_all_false(self):
        response = self.client.get("/user/permissions", user=self.user)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['view_public_extractions'])
        self.assertFalse(data['view_corp_extractions'])
        self.assertFalse(data['view_alliance_extractions'])
        self.assertFalse(data['view_observations'])
        self.assertFalse(data['su'])

    def test_view_public_extractions_perm(self):
        perm = Permission.objects.get_by_natural_key('view_available', 'moons', 'moonfrack')
        self.user.user_permissions.add(perm)
        response = self.client.get("/user/permissions", user=self.user)
        self.assertTrue(response.json()['view_public_extractions'])

    def test_view_corp_perm(self):
        perm = Permission.objects.get_by_natural_key('view_corp', 'moons', 'moonfrack')
        self.user.user_permissions.add(perm)
        response = self.client.get("/user/permissions", user=self.user)
        self.assertTrue(response.json()['view_corp_extractions'])

    def test_view_alliance_perm(self):
        perm = Permission.objects.get_by_natural_key('view_alliance', 'moons', 'moonfrack')
        self.user.user_permissions.add(perm)
        response = self.client.get("/user/permissions", user=self.user)
        self.assertTrue(response.json()['view_alliance_extractions'])

    def test_view_all_perm(self):
        perm = Permission.objects.get_by_natural_key('view_all', 'moons', 'moonfrack')
        self.user.user_permissions.add(perm)
        response = self.client.get("/user/permissions", user=self.user)
        self.assertTrue(response.json()['view_observations'])

    def test_superuser_flag(self):
        self.user.is_superuser = True
        self.user.save()
        response = self.client.get("/user/permissions", user=self.user)
        self.assertTrue(response.json()['su'])


class TestExtractionsEndpoint(TestCase):
    def setUp(self):
        self.client = TestClient(api)
        self.user = AuthUtils.create_user("extraction_user")
        self.view_available = Permission.objects.get_by_natural_key('view_available', 'moons', 'moonfrack')

    def test_no_perm_returns_empty(self):
        response = self.client.get("/extractions/", user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_with_perm_no_fracks_returns_empty(self):
        self.user.user_permissions.add(self.view_available)
        response = self.client.get("/extractions/", user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_with_perm_returns_recent_fracks(self):
        # view_available alone restricts to PUBLIC_MOON_CORPS; view_all bypasses that filter
        view_all = Permission.objects.get_by_natural_key('view_all', 'moons', 'moonfrack')
        self.user.user_permissions.set([self.view_available, view_all])
        _, _, _, moon = _build_geo_chain()
        corp_info = EveCorporationInfo.objects.create(
            corporation_id=10, corporation_name="Mining Corp",
            corporation_ticker="MN", member_count=1, ceo_id=1,
        )
        corp_audit = CorporationAudit.objects.create(corporation=corp_info)
        structure = EveLocation.objects.create(location_id=9000001, location_name="Drillhead Alpha")
        MoonFrack.objects.create(
            corporation=corp_audit, moon_id=moon.id, moon_name=moon,
            structure=structure,
            start_time=timezone.now() - timedelta(days=10),
            arrival_time=timezone.now() - timedelta(hours=2),
            auto_time=timezone.now() + timedelta(hours=12),
        )
        response = self.client.get("/extractions/", user=self.user)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['ObserverName'], "Drillhead Alpha")
        self.assertEqual(data[0]['moon']['id'], moon.id)

    def test_frack_older_than_3_days_not_returned(self):
        self.user.user_permissions.add(self.view_available)
        _, _, _, moon = _build_geo_chain()
        corp_info = EveCorporationInfo.objects.create(
            corporation_id=11, corporation_name="Old Corp",
            corporation_ticker="OLD", member_count=1, ceo_id=1,
        )
        corp_audit = CorporationAudit.objects.create(corporation=corp_info)
        structure = EveLocation.objects.create(location_id=9000002, location_name="Old Refinery")
        MoonFrack.objects.create(
            corporation=corp_audit, moon_id=moon.id, moon_name=moon,
            structure=structure,
            start_time=timezone.now() - timedelta(days=40),
            arrival_time=timezone.now() - timedelta(days=10),
            auto_time=timezone.now() - timedelta(days=9),
        )
        response = self.client.get("/extractions/", user=self.user)
        self.assertEqual(response.json(), [])


class TestPastExtractionsEndpoint(TestCase):
    def setUp(self):
        self.client = TestClient(api)
        self.user = AuthUtils.create_user("past_user")

    def test_no_perm_returns_empty(self):
        response = self.client.get("/extractions/past", user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_view_available_alone_returns_empty(self):
        perm = Permission.objects.get_by_natural_key('view_available', 'moons', 'moonfrack')
        self.user.user_permissions.add(perm)
        response = self.client.get("/extractions/past", user=self.user)
        self.assertEqual(response.json(), [])

    def test_view_all_perm_returns_data(self):
        perm = Permission.objects.get_by_natural_key('view_all', 'moons', 'moonfrack')
        self.user.user_permissions.add(perm)
        _, _, _, moon = _build_geo_chain()
        corp_info = EveCorporationInfo.objects.create(
            corporation_id=20, corporation_name="Past Corp",
            corporation_ticker="PST", member_count=1, ceo_id=1,
        )
        corp_audit = CorporationAudit.objects.create(corporation=corp_info)
        structure = EveLocation.objects.create(location_id=9000010, location_name="Past Refinery")
        MoonFrack.objects.create(
            corporation=corp_audit, moon_id=moon.id, moon_name=moon,
            structure=structure,
            start_time=timezone.now() - timedelta(days=60),
            arrival_time=timezone.now() - timedelta(days=30),
            auto_time=timezone.now() - timedelta(days=29),
        )
        response = self.client.get("/extractions/past", user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)


class TestFutureExtractionsEndpoint(TestCase):
    def setUp(self):
        self.client = TestClient(api)
        self.user = AuthUtils.create_user("future_user")

    def test_no_perm_returns_empty(self):
        response = self.client.get("/extractions/future", user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_view_all_returns_future_fracks(self):
        perm = Permission.objects.get_by_natural_key('view_all', 'moons', 'moonfrack')
        self.user.user_permissions.add(perm)
        _, _, _, moon = _build_geo_chain()
        corp_info = EveCorporationInfo.objects.create(
            corporation_id=30, corporation_name="Future Corp",
            corporation_ticker="FTR", member_count=1, ceo_id=1,
        )
        corp_audit = CorporationAudit.objects.create(corporation=corp_info)
        structure = EveLocation.objects.create(location_id=9000020, location_name="Future Refinery")
        MoonFrack.objects.create(
            corporation=corp_audit, moon_id=moon.id, moon_name=moon,
            structure=structure,
            start_time=timezone.now() - timedelta(days=14),
            arrival_time=timezone.now() + timedelta(days=2),
            auto_time=timezone.now() + timedelta(days=3),
        )
        response = self.client.get("/extractions/future", user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)


class TestSearchEndpoints(TestCase):
    def setUp(self):
        self.client = TestClient(api)
        self.user = AuthUtils.create_user("search_user")

    def test_moon_search_unauthenticated_returns_401(self):
        response = self.client.get("/moons/search?search_text=test")
        self.assertEqual(response.status_code, 401)

    def test_moon_search_returns_matching_moons(self):
        Moon.objects.create(id=50000001, name="Jita IV - Moon 4")
        Moon.objects.create(id=50000002, name="Dodixie IX - Moon 20")
        response = self.client.get("/moons/search?search_text=Jita", user=self.user)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], "Jita IV - Moon 4")

    def test_corporation_search(self):
        EveCorporationInfo.objects.create(
            corporation_id=40, corporation_name="Caldari State",
            corporation_ticker="CAL", member_count=1, ceo_id=1,
        )
        response = self.client.get("/corporations/search?search_text=Caldari", user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_character_search(self):
        EveCharacter.objects.create(
            character_id=9999, character_name="Space Miner Joe",
            corporation_id=1, corporation_name="NPC", corporation_ticker="NPC",
        )
        response = self.client.get("/characters/search?search_text=Space+Miner", user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search_limit_respected(self):
        for i in range(15):
            Moon.objects.create(id=60000000 + i, name=f"Jita IV - Moon {i}")
        response = self.client.get("/moons/search?search_text=Jita&limit=5", user=self.user)
        self.assertEqual(len(response.json()), 5)


class TestRentalEndpoints(TestCase):
    def setUp(self):
        self.client = TestClient(api)
        self.user = AuthUtils.create_user("rental_user")
        self.add_rental_perm = Permission.objects.get_by_natural_key('add_moonrental', 'moons', 'moonrental')

    def test_list_no_perm_returns_empty(self):
        response = self.client.get("/rental/list", user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_invalid_no_perm_returns_empty(self):
        response = self.client.get("/rental/invalid", user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_list_returns_active_rentals(self):
        self.user.user_permissions.add(self.add_rental_perm)
        _, _, system, moon = _build_geo_chain()
        corp = EveCorporationInfo.objects.create(
            corporation_id=50, corporation_name="Renter Corp",
            corporation_ticker="RNT", member_count=1, ceo_id=1,
        )
        char = EveCharacter.objects.create(
            character_id=8001, character_name="Rich Renter",
            corporation_id=50, corporation_name="Renter Corp", corporation_ticker="RNT",
        )
        MoonRental.objects.create(
            moon=moon, contact=char, corporation=corp,
            price=100_000_000, start_date=timezone.now(), note="",
        )
        response = self.client.get("/rental/list", user=self.user)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['moon']['name'], moon.name)

    def test_list_excludes_ended_rentals(self):
        self.user.user_permissions.add(self.add_rental_perm)
        _, _, system, moon = _build_geo_chain()
        corp = EveCorporationInfo.objects.create(
            corporation_id=51, corporation_name="Ex Renter Corp",
            corporation_ticker="EXR", member_count=1, ceo_id=1,
        )
        char = EveCharacter.objects.create(
            character_id=8002, character_name="Ex Renter",
            corporation_id=51, corporation_name="Ex Renter Corp", corporation_ticker="EXR",
        )
        MoonRental.objects.create(
            moon=moon, contact=char, corporation=corp,
            price=100_000_000, start_date=timezone.now() - timedelta(days=30),
            end_date=timezone.now() - timedelta(days=1), note="",
        )
        response = self.client.get("/rental/list", user=self.user)
        self.assertEqual(response.json(), [])


class TestAdminEndpoints(TestCase):
    def setUp(self):
        self.client = TestClient(api)
        self.user = AuthUtils.create_user("admin_user")
        self.superuser = AuthUtils.create_user("super_user")
        self.superuser.is_superuser = True
        self.superuser.save()

    def test_explain_non_superuser_returns_403(self):
        response = self.client.get("/admin/explain", user=self.user)
        self.assertEqual(response.status_code, 403)

    def test_outstanding_non_superuser_returns_403(self):
        response = self.client.get("/admin/outstanding", user=self.user)
        self.assertEqual(response.status_code, 403)

    def test_corp_list_non_superuser_returns_403(self):
        response = self.client.get("/admin/list", user=self.user)
        self.assertEqual(response.status_code, 403)

    def test_explain_superuser_returns_structure(self):
        response = self.client.get("/admin/explain", user=self.superuser)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('structures', data)
        self.assertIn('taxes', data)

    def test_outstanding_superuser_returns_list(self):
        response = self.client.get("/admin/outstanding", user=self.superuser)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
