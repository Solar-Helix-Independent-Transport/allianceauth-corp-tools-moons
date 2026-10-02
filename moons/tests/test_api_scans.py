from decimal import Decimal

from eve_sde.models import (
    Constellation, ItemGroup, ItemType, Moon, Region, SolarSystem,
)
from ninja.testing import TestClient

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from allianceauth.tests.auth_utils import AuthUtils

from moons.api import api
from moons.models import MoonScan

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
