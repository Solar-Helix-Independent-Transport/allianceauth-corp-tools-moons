from decimal import Decimal
from pathlib import Path

from eve_sde.models import (
    Constellation, DogmaAttribute, ItemGroup, ItemType, Moon, Region,
    SolarSystem, TypeDogma,
)

from django.contrib.auth.models import Permission
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from allianceauth.tests.auth_utils import AuthUtils

from moons.models import MoonScan, OrePrice, OreTax, OreTaxRates
from moons.scans import (
    commit_import, moon_values, parse_moon_scan, preview_import,
)

FIXTURES = Path(__file__).parent / "fixtures" / "scans"


def _fixture(name):
    # newline="" keeps CRLF exactly as pasted
    with open(FIXTURES / name, encoding="utf-8", newline="") as f:
        return f.read()


class TestParseMoonScan(SimpleTestCase):
    def test_english_multi_moon_paste_with_header_and_crlf(self):
        moons = parse_moon_scan(_fixture("en_multi_moon_crlf.txt"))

        self.assertEqual([m.moon_id for m in moons], [40161708, 40161709])
        self.assertEqual(moons[0].name, "Auga V - Moon 1")
        self.assertEqual(
            moons[0].ores,
            {
                45506: Decimal("0.19"),
                46676: Decimal("0.23"),
                46678: Decimal("0.25"),
                46689: Decimal("0.33"),
            },
        )
        self.assertEqual(moons[1].name, "Auga V - Moon 2")
        self.assertEqual(
            moons[1].ores,
            {
                45492: Decimal("0.27"),
                45494: Decimal("0.23"),
                46676: Decimal("0.21"),
                46678: Decimal("0.29"),
            },
        )

    def test_paste_without_header_row(self):
        moons = parse_moon_scan(_fixture("en_no_header_lf.txt"))

        self.assertEqual(len(moons), 1)
        self.assertEqual(moons[0].moon_id, 40217116)
        self.assertEqual(moons[0].name, "Erstet IX - Moon 4")
        self.assertEqual(
            moons[0].ores,
            {
                45493: Decimal("0.239822223783"),
                45499: Decimal("0.557235956192"),
                45490: Decimal("0.202941834927"),
            },
        )

    def test_tabs_mangled_into_four_spaces(self):
        moons = parse_moon_scan(_fixture("en_single_moon_quad_spaces.txt"))

        self.assertEqual(len(moons), 1)
        self.assertEqual(moons[0].moon_id, 40131695)
        self.assertEqual(moons[0].name, "Helgatild IX - Moon 12")
        self.assertEqual(
            moons[0].ores,
            {
                45495: Decimal("0.111999601126"),
                45491: Decimal("0.211025685072"),
                45510: Decimal("0.176974713802"),
            },
        )

    def test_localised_client_uses_english_hints(self):
        for name in ("fr_localized_hint_tabs.txt", "fr_localized_hint_quad_spaces.txt"):
            with self.subTest(name):
                moons = parse_moon_scan(_fixture(name))

                self.assertEqual([m.moon_id for m in moons], [40128179, 40128225])
                self.assertEqual(moons[0].name, "OE-9UF IV - Moon 14")
                self.assertEqual(moons[0].ores[45504], Decimal("0.334263443947"))
                self.assertEqual(moons[0].ores[45499], Decimal("0.284777760506"))
                self.assertEqual(moons[0].ores[45496], Decimal("0.162188977003"))
                self.assertEqual(moons[1].name, "PFU-LH IV - Moon 8")
                self.assertEqual(moons[1].ores[45496], Decimal("0.397391051054"))


MOON_1 = 40161708
MOON_2 = 40161709
CINNABAR, BITUMENS, COBALTITE = 45506, 45492, 45494
CUBIC_BISTOT = 46676  # exists, but no longer a moon ore


def _paste(*moons):
    """moons: (moon_id, {type_id: fraction_str})"""
    lines = ["Moon\tMoon Product\tQuantity\tOre TypeID\tSolarSystemID\tPlanetID\tMoonID"]
    for moon_id, ores in moons:
        lines.append(f"Moon {moon_id}")
        for type_id, fraction in ores.items():
            lines.append(f"\tOre\t{fraction}\t{type_id}\t30002542\t40161707\t{moon_id}")
    return "\r\n".join(lines)


class TestImportScans(TestCase):
    @classmethod
    def setUpTestData(cls):
        region = Region.objects.create(id=10000001, name="Test Region")
        constellation = Constellation.objects.create(id=20000001, name="Test Constellation", region=region)
        system = SolarSystem.objects.create(id=30002542, name="Auga", constellation=constellation)
        Moon.objects.create(id=MOON_1, name="Auga V - Moon 1", solar_system=system)
        Moon.objects.create(id=MOON_2, name="Auga V - Moon 2", solar_system=system)

        ubiq = ItemGroup.objects.create(id=1884, name="Ubiquitous Moon Asteroids")
        common = ItemGroup.objects.create(id=1920, name="Common Moon Asteroids")
        rare = ItemGroup.objects.create(id=1922, name="Rare Moon Asteroids")
        bistot = ItemGroup.objects.create(id=451, name="Bistot")
        ItemType.objects.create(id=CINNABAR, name="Cinnabar", group=rare)
        ItemType.objects.create(id=BITUMENS, name="Bitumens", group=ubiq)
        ItemType.objects.create(id=COBALTITE, name="Cobaltite", group=common)
        ItemType.objects.create(id=CUBIC_BISTOT, name="Cubic Bistot", group=bistot)

        cls.adder = AuthUtils.create_user("scan_adder")
        cls.adder.user_permissions.add(
            Permission.objects.get_by_natural_key("add_moonscan", "moons", "moonscan"))
        cls.changer = AuthUtils.create_user("scan_changer")
        cls.changer.user_permissions.add(
            Permission.objects.get_by_natural_key("add_moonscan", "moons", "moonscan"),
            Permission.objects.get_by_natural_key("change_moonscan", "moons", "moonscan"))
        cls.other_adder = AuthUtils.create_user("other_scan_adder")
        cls.other_adder.user_permissions.add(
            Permission.objects.get_by_natural_key("add_moonscan", "moons", "moonscan"))

    def test_preview_of_unscanned_moon_is_new_and_writes_nothing(self):
        results = preview_import(_paste((MOON_1, {CINNABAR: "0.4", BITUMENS: "0.6"})), self.adder)

        self.assertEqual([(r.moon_id, r.name, r.status) for r in results],
                         [(MOON_1, "Auga V - Moon 1", "new")])
        self.assertFalse(MoonScan.objects.exists())

    def test_commit_stores_scan_with_who_added_it_and_exact_fractions(self):
        results = commit_import(
            _paste((MOON_1, {CINNABAR: "0.193847562011", BITUMENS: "0.6"})), self.adder)

        self.assertEqual([r.status for r in results], ["new"])
        scan = MoonScan.objects.get(moon_id=MOON_1)
        self.assertEqual(scan.added_by, self.adder)
        self.assertIsNotNone(scan.added_at)
        self.assertEqual(
            {o.ore_id: o.fraction for o in scan.ores.all()},
            {CINNABAR: Decimal("0.193847562011"), BITUMENS: Decimal("0.600000000000")},
        )

    def test_reimport_matching_to_four_places_is_unchanged_and_keeps_original_submitter(self):
        commit_import(_paste((MOON_1, {CINNABAR: "0.193847562011", BITUMENS: "0.6"})), self.adder)
        original = MoonScan.objects.get(moon_id=MOON_1)

        results = commit_import(
            _paste((MOON_1, {CINNABAR: "0.19384", BITUMENS: "0.600049"})), self.other_adder)

        self.assertEqual([r.status for r in results], ["unchanged"])
        scan = MoonScan.objects.get(moon_id=MOON_1)
        self.assertEqual(scan.added_by, self.adder)
        self.assertEqual(scan.added_at, original.added_at)
        self.assertEqual(scan.ores.get(ore_id=CINNABAR).fraction, Decimal("0.193847562011"))

    def test_changed_composition_replaces_scan_for_user_with_change_permission(self):
        commit_import(_paste((MOON_1, {CINNABAR: "0.4", BITUMENS: "0.6"})), self.adder)

        preview = preview_import(_paste((MOON_1, {COBALTITE: "0.5", BITUMENS: "0.5"})), self.changer)
        self.assertEqual([r.status for r in preview], ["changed"])

        commit_import(_paste((MOON_1, {COBALTITE: "0.5", BITUMENS: "0.5"})), self.changer)

        scan = MoonScan.objects.get(moon_id=MOON_1)
        self.assertEqual(scan.added_by, self.changer)
        self.assertEqual(
            {o.ore_id: o.fraction for o in scan.ores.all()},
            {COBALTITE: Decimal("0.5"), BITUMENS: Decimal("0.5")},
        )

    def test_changed_moon_is_skipped_without_change_permission_but_new_moons_still_import(self):
        commit_import(_paste((MOON_1, {CINNABAR: "0.4", BITUMENS: "0.6"})), self.adder)

        results = commit_import(
            _paste(
                (MOON_1, {COBALTITE: "0.5", BITUMENS: "0.5"}),
                (MOON_2, {BITUMENS: "0.3"}),
            ),
            self.other_adder,
        )

        self.assertEqual([(r.moon_id, r.status) for r in results],
                         [(MOON_1, "needs_change_perm"), (MOON_2, "new")])
        self.assertEqual(MoonScan.objects.get(moon_id=MOON_1).added_by, self.adder)
        self.assertEqual(
            set(MoonScan.objects.get(moon_id=MOON_1).ores.values_list("ore_id", flat=True)),
            {CINNABAR, BITUMENS},
        )
        self.assertEqual(MoonScan.objects.get(moon_id=MOON_2).added_by, self.other_adder)

    def test_unknown_moon_and_unknown_ore_type_are_rejected_with_a_reason(self):
        results = commit_import(
            _paste(
                (49999999, {BITUMENS: "0.5"}),
                (MOON_1, {BITUMENS: "0.5", 99999: "0.2"}),
                (MOON_2, {BITUMENS: "0.3"}),
            ),
            self.adder,
        )

        self.assertEqual([(r.moon_id, r.status) for r in results],
                         [(49999999, "rejected"), (MOON_1, "rejected"), (MOON_2, "new")])
        self.assertEqual(results[0].name, "Moon 49999999")  # heading from the paste
        self.assertIn("Unknown moon", results[0].reason)
        self.assertIn("99999", results[1].reason)
        self.assertEqual(list(MoonScan.objects.values_list("moon_id", flat=True)), [MOON_2])

    def test_ore_that_is_no_longer_a_moon_ore_is_accepted_and_flagged(self):
        results = commit_import(_paste((MOON_1, {CINNABAR: "0.4", CUBIC_BISTOT: "0.3"})), self.adder)

        self.assertEqual(results[0].status, "new")
        self.assertEqual(results[0].flagged, ["Cubic Bistot"])
        self.assertEqual(
            set(MoonScan.objects.get(moon_id=MOON_1).ores.values_list("ore_id", flat=True)),
            {CINNABAR, CUBIC_BISTOT},
        )


class TestMoonValues(TestCase):
    """Worked by hand: a 30 day pull at 40,000 m3/h is 28,800,000 m3,
    i.e. 2,880,000 units of 10 m3 ore per 1.0 of composition."""

    @classmethod
    def setUpTestData(cls):
        region = Region.objects.create(id=10000001, name="Test Region")
        constellation = Constellation.objects.create(id=20000001, name="Test Constellation", region=region)
        system = SolarSystem.objects.create(id=30002542, name="Auga", constellation=constellation)
        cls.moon = Moon.objects.create(id=MOON_1, name="Auga V - Moon 1", solar_system=system)
        rare = ItemGroup.objects.create(id=1922, name="Rare Moon Asteroids")
        ubiq = ItemGroup.objects.create(id=1884, name="Ubiquitous Moon Asteroids")
        cls.cinnabar = ItemType.objects.create(id=CINNABAR, name="Cinnabar", group=rare)
        cls.bitumens = ItemType.objects.create(id=BITUMENS, name="Bitumens", group=ubiq)
        cls.user = AuthUtils.create_user("valuer")

        cls.profile = OreTaxRates.objects.create(
            tag="Rental", refine_rate=Decimal("87.5"), ore_rate=0, ubiquitous_rate=10,
            common_rate=0, uncommon_rate=0, rare_rate=20, exceptional_rate=0,
            show_in_moon_values=True)
        OrePrice.objects.create(item=cls.cinnabar, price=Decimal("1000"))
        OrePrice.objects.create(item=cls.cinnabar, price=Decimal("800"), goo_only=True)
        OrePrice.objects.create(item=cls.bitumens, price=Decimal("100"))
        OreTax.objects.create(item=cls.cinnabar, tax=cls.profile, price=Decimal("175"))
        OreTax.objects.create(item=cls.bitumens, tax=cls.profile, price=Decimal("8.75"))

    def _scan(self, ores):
        scan = MoonScan.objects.create(moon=self.moon, added_by=self.user, added_at=timezone.now())
        for ore, fraction in ores.items():
            scan.ores.create(ore_id=ore, fraction=Decimal(fraction))
        return scan

    def test_value_and_tax_per_30_days(self):
        self._scan({CINNABAR: "0.5", BITUMENS: "0.5"})

        [moon] = moon_values(self.profile)

        # 1,440,000 units each; value at 87.5% refine: 875 + 87.5 per unit
        self.assertEqual(moon.moon_id, MOON_1)
        self.assertEqual(moon.value_30d, Decimal("1386000000"))
        # tax uses the stored per-unit OreTax: 175 + 8.75 per unit
        self.assertEqual(moon.tax_30d, Decimal("264600000"))
        self.assertEqual(moon.added_by, self.user)
        self.assertEqual(moon.unpriced, [])

    def test_profile_ignoring_ores_in_refine_uses_goo_only_price(self):
        self._scan({CINNABAR: "0.5"})
        self.profile.ignore_ores_in_refine = True

        [moon] = moon_values(self.profile)

        # 1,440,000 units at 800 goo-only * 87.5%
        self.assertEqual(moon.value_30d, Decimal("1008000000"))

    def test_partial_composition_is_not_scaled_up(self):
        self._scan({CINNABAR: "0.25"})

        [moon] = moon_values(self.profile)

        # 720,000 units at 875
        self.assertEqual(moon.value_30d, Decimal("630000000"))
        self.assertEqual(moon.total_fraction, Decimal("0.25"))

    def test_ore_without_a_price_is_zero_and_listed(self):
        rare = ItemGroup.objects.get(id=1922)
        ItemType.objects.create(id=45510, name="Xenotime", group=rare)
        self._scan({CINNABAR: "0.25", 45510: "0.5"})

        [moon] = moon_values(self.profile)

        self.assertEqual(moon.value_30d, Decimal("630000000"))
        self.assertEqual(moon.unpriced, ["Xenotime"])

    @override_settings(MOONS_DRILL_M3_PER_HOUR=20000)
    def test_drill_rate_setting(self):
        self._scan({CINNABAR: "0.5"})

        [moon] = moon_values(self.profile)

        # 720,000 units at 875
        self.assertEqual(moon.value_30d, Decimal("630000000"))

    def test_profile_taxing_base_ore_values_jackpot_variant_at_base_price(self):
        jackpot = ItemType.objects.create(
            id=46311, name="Glistening Cinnabar", group=ItemGroup.objects.get(id=1922))
        attr = DogmaAttribute.objects.create(id=2711, name="oreBasicType")
        TypeDogma.objects.create(item_type=jackpot, dogma_attribute=attr, value=CINNABAR)
        OrePrice.objects.create(item=jackpot, price=Decimal("2000"))
        self._scan({46311: "0.5"})
        self.profile.tax_on_base_ore_value = True

        [moon] = moon_values(self.profile)

        # priced as plain Cinnabar: 1,440,000 units at 875
        self.assertEqual(moon.value_30d, Decimal("1260000000"))
