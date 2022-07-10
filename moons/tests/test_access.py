from datetime import timedelta
from unittest import mock
from corptools.models import CorporationAudit, EveLocation
from django.test import TestCase
from allianceauth.tests.auth_utils import AuthUtils
from ..models import MoonFrack
from django.contrib.auth.models import Permission
from django.utils import timezone
from allianceauth.eveonline.models import EveAllianceInfo, EveCharacter, EveCorporationInfo
from allianceauth.authentication.models import CharacterOwnership


class TestInvoicesAccessPerms(TestCase):
    def setUp(cls):
        cls.user1 = AuthUtils.create_user('Main User1')
        cls.user2 = AuthUtils.create_user('Main User2')
        cls.user3 = AuthUtils.create_user('Main User3')
        cls.user4 = AuthUtils.create_user('Main User4')
        cls.user5 = AuthUtils.create_user('Main User5')

        corp1 = EveCorporationInfo.objects.create(corporation_id=123,
                                                  corporation_name='corporation.name1',
                                                  corporation_ticker='ABC',
                                                  member_count=1,
                                                  ceo_id=1,
                                                  )

        char1 = EveCharacter.objects.create(character_id=1,
                                            character_name='character.name1',
                                            corporation_id=123,
                                            corporation_name='corporation.name1',
                                            corporation_ticker='ABC')
        char2 = EveCharacter.objects.create(character_id=2,
                                            character_name='character.name2',
                                            corporation_id=123,
                                            corporation_name='corporation.name1',
                                            corporation_ticker='ABC')

        alli1 = EveAllianceInfo.objects.create(alliance_id=3,
                                               alliance_name="test alliance",
                                               alliance_ticker="TEST",
                                               executor_corp_id=2
                                               )
        corp2 = EveCorporationInfo.objects.create(corporation_id=2,
                                                  corporation_name='corporation.name2',
                                                  corporation_ticker='ABC2',
                                                  member_count=1,
                                                  ceo_id=1,
                                                  alliance=alli1
                                                  )

        char3 = EveCharacter.objects.create(character_id=3,
                                            character_name='character.name3',
                                            corporation_id=2,
                                            corporation_name='corporation.name2',
                                            corporation_ticker='ABC2',
                                            alliance_id=3,
                                            alliance_name='test alliance',
                                            alliance_ticker='TEST')
        char4 = EveCharacter.objects.create(character_id=4,
                                            character_name='character.name4',
                                            corporation_id=2,
                                            corporation_name='corporation.name2',
                                            corporation_ticker='ABC',
                                            alliance_id=4,
                                            alliance_name='test alliance2',
                                            alliance_ticker='TEST')

        alli2 = EveAllianceInfo.objects.create(alliance_id=4,
                                               alliance_name="test alliance2",
                                               alliance_ticker="TEST2",
                                               executor_corp_id=3
                                               )
        corp3 = EveCorporationInfo.objects.create(corporation_id=3,
                                                  corporation_name='corporation.name3',
                                                  corporation_ticker='ABC3',
                                                  member_count=1,
                                                  ceo_id=1,
                                                  alliance=alli2
                                                  )

        char5 = EveCharacter.objects.create(character_id=5,
                                            character_name='character.name5',
                                            corporation_id=3,
                                            corporation_name='corporation.name3',
                                            corporation_ticker='ABC3',
                                            alliance_id=4,
                                            alliance_name='test alliance2',
                                            alliance_ticker='TEST')
        char6 = EveCharacter.objects.create(character_id=6,
                                            character_name='character.name6',
                                            corporation_id=3,
                                            corporation_name='corporation.name3',
                                            corporation_ticker='ABC3',
                                            alliance_id=4,
                                            alliance_name='test alliance2',
                                            alliance_ticker='TEST2')

        corp4 = EveCorporationInfo.objects.create(corporation_id=4,
                                                  corporation_name='corporation.name4',
                                                  corporation_ticker='ABC4',
                                                  member_count=1,
                                                  ceo_id=1,
                                                  alliance=alli2
                                                  )

        char7 = EveCharacter.objects.create(character_id=7,
                                            character_name='character.name7',
                                            corporation_id=4,
                                            corporation_name='corporation.name4',
                                            corporation_ticker='ABC4',
                                            alliance_id=4,
                                            alliance_name='test alliance2',
                                            alliance_ticker='TEST2')
        char9 = EveCharacter.objects.create(character_id=9,
                                            character_name='character.name9',
                                            corporation_id=4,
                                            corporation_name='corporation.name4',
                                            corporation_ticker='ABC4',
                                            alliance_id=4,
                                            alliance_name='test alliance2',
                                            alliance_ticker='TEST2'
                                            )

        alli3 = EveAllianceInfo.objects.create(alliance_id=5,
                                               alliance_name="test alliance3",
                                               alliance_ticker="TEST3",
                                               executor_corp_id=4
                                               )
        corp5 = EveCorporationInfo.objects.create(corporation_id=5,
                                                  corporation_name='corporation.name5',
                                                  corporation_ticker='ABC5',
                                                  member_count=1,
                                                  ceo_id=1,
                                                  alliance=alli3
                                                  )
        char8 = EveCharacter.objects.create(character_id=8,
                                            character_name='character.name8',
                                            corporation_id=5,
                                            corporation_name='corporation.name5',
                                            corporation_ticker='ABC5',
                                            alliance_id=5,
                                            alliance_name='test alliance3',
                                            alliance_ticker='TEST3')

        # User 1 - Char 1 and 2 ( Corp 1 no alliance )
        cls.user1.profile.main_character = char1
        CharacterOwnership.objects.create(
            user=cls.user1, character=char1, owner_hash="abc123")
        cls.user1.profile.save()
        CharacterOwnership.objects.create(
            user=cls.user1, character=char2, owner_hash="cba123")
        cls.user1.profile.refresh_from_db()

        # User 2 - Char 3 ( Corp 2, Alliance 1 )
        cls.user2.profile.main_character = char3
        CharacterOwnership.objects.create(
            user=cls.user2, character=char3, owner_hash="cba321")
        cls.user2.profile.save()
        cls.user2.profile.refresh_from_db()

        # User 3 - Char 5 and 7 ( Corp 3 and 4, Alliance 2 )
        cls.user3.profile.main_character = char5
        CharacterOwnership.objects.create(
            user=cls.user3, character=char5, owner_hash="abc432")
        cls.user3.profile.save()
        CharacterOwnership.objects.create(
            user=cls.user3, character=char7, owner_hash="def432")
        cls.user3.profile.refresh_from_db()

        # User 4 - Char 9 and 8 ( Corp 4, 5 Alliance 2, 3)
        cls.user4.profile.main_character = char9
        CharacterOwnership.objects.create(
            user=cls.user4, character=char9, owner_hash="tre456")
        CharacterOwnership.objects.create(
            user=cls.user4, character=char8, owner_hash="wer456")
        cls.user4.profile.save()
        cls.user3.profile.refresh_from_db()

        # User 5 - no characters

        ca1 = CorporationAudit.objects.create(
            corporation=corp1
        )
        ca2 = CorporationAudit.objects.create(
            corporation=corp2
        )
        ca3 = CorporationAudit.objects.create(
            corporation=corp3
        )
        ca4 = CorporationAudit.objects.create(
            corporation=corp4
        )

        cls.view_available_permission = Permission.objects.get_by_natural_key(
            'view_available', 'moons', 'moonfrack')
        cls.view_corp_permission = Permission.objects.get_by_natural_key(
            'view_corp', 'moons', 'moonfrack')
        cls.view_alliance_permission = Permission.objects.get_by_natural_key(
            'view_alliance', 'moons', 'moonfrack')
        cls.view_all_permission = Permission.objects.get_by_natural_key(
            'view_all', 'moons', 'moonfrack')

        cls.user1.user_permissions.add(cls.view_available_permission)

        el1 = EveLocation.objects.create(
            location_id=1,
            location_name="test1"
        )
        el2 = EveLocation.objects.create(
            location_id=2,
            location_name="test2"
        )
        el3 = EveLocation.objects.create(
            location_id=3,
            location_name="test3"
        )
        el4 = EveLocation.objects.create(
            location_id=4,
            location_name="test4"
        )
        el4 = EveLocation.objects.create(
            location_id=5,
            location_name="test5"
        )

        cls.mf1 = MoonFrack.objects.create(
            corporation=ca1,
            moon_id=123,
            structure=el1,
            start_time=timezone.now()-timedelta(days=30),
            arrival_time=timezone.now()-timedelta(hours=1),
            auto_time=timezone.now()
        )
        cls.mf2 = MoonFrack.objects.create(
            corporation=ca2,
            moon_id=456,
            structure=el2,
            start_time=timezone.now()-timedelta(days=30),
            arrival_time=timezone.now()-timedelta(hours=1),
            auto_time=timezone.now()
        )
        cls.mf3 = MoonFrack.objects.create(
            corporation=ca3,
            moon_id=789,
            structure=el3,
            start_time=timezone.now()-timedelta(days=30),
            arrival_time=timezone.now()-timedelta(hours=1),
            auto_time=timezone.now()
        )
        cls.mf4 = MoonFrack.objects.create(
            corporation=ca4,
            moon_id=101,
            structure=el4,
            start_time=timezone.now()-timedelta(days=30),
            arrival_time=timezone.now()-timedelta(hours=1),
            auto_time=timezone.now()
        )

    def test_get_corp_in_alliance(self):
        self.user2.user_permissions.add(self.view_corp_permission)
        cs = MoonFrack.objects.visible_to(self.user2)
        self.assertNotIn(self.mf1, cs)
        self.assertIn(self.mf2, cs)
        self.assertNotIn(self.mf3, cs)
        self.assertNotIn(self.mf4, cs)

    def test_get_corp_in_alliance_with_alliance(self):
        self.user2.user_permissions.add(self.view_alliance_permission)
        cs = MoonFrack.objects.visible_to(self.user2)
        self.assertNotIn(self.mf1, cs)
        self.assertIn(self.mf2, cs)
        self.assertNotIn(self.mf3, cs)
        self.assertNotIn(self.mf4, cs)

    def test_get_alliance_no_alliance(self):
        self.user1.user_permissions.add(self.view_alliance_permission)
        cs = MoonFrack.objects.visible_to(self.user1)
        self.assertIn(self.mf1, cs)
        self.assertNotIn(self.mf2, cs)
        self.assertNotIn(self.mf3, cs)
        self.assertNotIn(self.mf4, cs)

    def test_get_alliance(self):
        self.user3.user_permissions.add(self.view_alliance_permission)
        cs = MoonFrack.objects.visible_to(self.user3)
        self.assertNotIn(self.mf1, cs)
        self.assertNotIn(self.mf2, cs)
        self.assertIn(self.mf3, cs)
        self.assertIn(self.mf4, cs)

    def test_get_alliance_with_corp(self):
        self.user3.user_permissions.add(self.view_alliance_permission)
        self.user3.user_permissions.add(self.view_corp_permission)
        cs = MoonFrack.objects.visible_to(self.user3)
        self.assertNotIn(self.mf1, cs)
        self.assertNotIn(self.mf2, cs)
        self.assertIn(self.mf3, cs)
        self.assertIn(self.mf4, cs)

    def test_global_perms_u1(self):
        self.user1.user_permissions.add(self.view_all_permission)
        cs = MoonFrack.objects.visible_to(self.user1)
        self.assertIn(self.mf1, cs)
        self.assertIn(self.mf2, cs)
        self.assertIn(self.mf3, cs)
        self.assertIn(self.mf4, cs)

    def test_global_perms_u2(self):
        self.user2.user_permissions.add(self.view_all_permission)
        cs = MoonFrack.objects.visible_to(self.user2)
        self.assertIn(self.mf1, cs)
        self.assertIn(self.mf2, cs)
        self.assertIn(self.mf3, cs)
        self.assertIn(self.mf4, cs)

    def test_global_perms_u3(self):
        self.user3.user_permissions.add(self.view_all_permission)
        cs = MoonFrack.objects.visible_to(self.user3)
        self.assertIn(self.mf1, cs)
        self.assertIn(self.mf2, cs)
        self.assertIn(self.mf3, cs)
        self.assertIn(self.mf4, cs)

    def test_su_perms(self):
        cs = MoonFrack.objects.visible_to(self.user5)
        self.assertNotIn(self.mf1, cs)
        self.assertNotIn(self.mf2, cs)
        self.assertNotIn(self.mf3, cs)
        self.assertNotIn(self.mf4, cs)

        self.user5.is_superuser = True

        cs = MoonFrack.objects.visible_to(self.user5)
        self.assertIn(self.mf1, cs)
        self.assertIn(self.mf2, cs)
        self.assertIn(self.mf3, cs)
        self.assertIn(self.mf4, cs)
