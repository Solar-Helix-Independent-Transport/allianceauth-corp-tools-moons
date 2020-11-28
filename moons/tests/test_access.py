from unittest import mock
from django.test import TestCase
from allianceauth.tests.auth_utils import AuthUtils
from ..models import Invoice
from django.contrib.auth.models import Permission
from django.utils import timezone
from allianceauth.eveonline.models import EveCharacter
from allianceauth.authentication.models import CharacterOwnership

class TestInvoicesAccessPerms(TestCase): 
    def setUp(cls):
        cls.user1 = AuthUtils.create_user('Main User1')
        cls.user2 = AuthUtils.create_user('Main User2')
        cls.user3 = AuthUtils.create_user('Main User3')
        cls.user4 = AuthUtils.create_user('Main User4')
        cls.user5 = AuthUtils.create_user('Main User5')
        
        char1 = EveCharacter.objects.create(character_id=1,
            character_name='character.name1',
            corporation_id=123,
            corporation_name='corporation.name1',
            corporation_ticker='ABC')
        cls.ci1 = Invoice.objects.create(character=char1, amount=5, due_date=timezone.now())

        cls.user1.profile.main_character = char1
        CharacterOwnership.objects.create(user=cls.user1, character=char1, owner_hash="abc123")
        cls.user1.profile.save()

        char2 = EveCharacter.objects.create(character_id=2,
            character_name='character.name2',
            corporation_id=123,
            corporation_name='corporation.name1',            
            corporation_ticker='ABC')
        cls.ci2 = Invoice.objects.create(character=char2, amount=5, due_date=timezone.now())
        CharacterOwnership.objects.create(user=cls.user1, character=char2, owner_hash="cba123")
        cls.user1.profile.refresh_from_db()

        char3 = EveCharacter.objects.create(character_id=3,
            character_name='character.name3',
            corporation_id=2,
            corporation_name='corporation.name2',            
            corporation_ticker='ABC2',            
            alliance_id=3, 
            alliance_name='test alliance2', 
            alliance_ticker='TEST')
        cls.ci3 = Invoice.objects.create(character=char3, amount=5, due_date=timezone.now())

        cls.user2.profile.main_character = char3
        CharacterOwnership.objects.create(user=cls.user2, character=char3, owner_hash="cba321")

        cls.user2.profile.save()
        cls.user2.profile.refresh_from_db()
        
        char4 = EveCharacter.objects.create(character_id=4,
            character_name='character.name4',
            corporation_id=2,
            corporation_name='corporation.name2',            
            corporation_ticker='ABC',            
            alliance_id=3, 
            alliance_name='test alliance2', 
            alliance_ticker='TEST')
        cls.ci4 = Invoice.objects.create(character=char4, amount=5, due_date=timezone.now())

        char5 = EveCharacter.objects.create(character_id=5,
            character_name='character.name5',
            corporation_id=3,
            corporation_name='corporation.name3',            
            corporation_ticker='ABC3',            
            alliance_id=4, 
            alliance_name='test alliance2', 
            alliance_ticker='TEST')
        cls.ci5 = Invoice.objects.create(character=char5, amount=5, due_date=timezone.now())

        cls.user3.profile.main_character = char5
        CharacterOwnership.objects.create(user=cls.user3, character=char5, owner_hash="abc432")

        cls.user3.profile.save()
        cls.user3.profile.refresh_from_db()

        char6 = EveCharacter.objects.create(character_id=6,
            character_name='character.name6',
            corporation_id=3,
            corporation_name='corporation.name3',            
            corporation_ticker='ABC3',            
            alliance_id=4, 
            alliance_name='test alliance2', 
            alliance_ticker='TEST2')
        cls.ci6 = Invoice.objects.create(character=char6, amount=5, due_date=timezone.now())

        char7 = EveCharacter.objects.create(character_id=7,
            character_name='character.name7',
            corporation_id=4,
            corporation_name='corporation.name4',            
            corporation_ticker='ABC4',            
            alliance_id=4, 
            alliance_name='test alliance2', 
            alliance_ticker='TEST2')
        cls.ci7 = Invoice.objects.create(character=char7, amount=5, due_date=timezone.now())
        CharacterOwnership.objects.create(user=cls.user3, character=char7, owner_hash="def432")

        char8 = EveCharacter.objects.create(character_id=8,
            character_name='character.name8',
            corporation_id=5,
            corporation_name='corporation.name5',            
            corporation_ticker='ABC5',            
            alliance_id=3, 
            alliance_name='test alliance3', 
            alliance_ticker='TEST3')
        cls.ci8 = Invoice.objects.create(character=char8, amount=5, due_date=timezone.now())

        cls.view_corp_permission = Permission.objects.get_by_natural_key('view_corp', 'invoices', 'invoice')
        cls.view_alliance_permission = Permission.objects.get_by_natural_key('view_alliance', 'invoices', 'invoice')
        cls.view_all_permission = Permission.objects.get_by_natural_key('view_all', 'invoices', 'invoice')

        char9 = EveCharacter.objects.create(character_id=9,
            character_name='character.name9',
            corporation_id=4,
            corporation_name='corporation.name4',            
            corporation_ticker='ABC4')
        cls.ci9 = Invoice.objects.create(character=char9, amount=5, due_date=timezone.now())
        cls.user4.profile.main_character = char9
        CharacterOwnership.objects.create(user=cls.user4, character=char9, owner_hash="tre456")
        cls.user4.profile.save()


    def test_no_perms_get_self_u1(self):  # always get self.
        cs = Invoice.objects.visible_to(self.user1)
        self.assertIn(self.ci1, cs)
        self.assertIn(self.ci2, cs)
        self.assertNotIn(self.ci3, cs)
        self.assertNotIn(self.ci4, cs)
        self.assertNotIn(self.ci5, cs)
        self.assertNotIn(self.ci6, cs)
        self.assertNotIn(self.ci7, cs)
        self.assertNotIn(self.ci8, cs)

    def test_no_perms_get_self_u2(self):  # always get self.
        cs = Invoice.objects.visible_to(self.user2)
        self.assertNotIn(self.ci1, cs)
        self.assertNotIn(self.ci2, cs)
        self.assertIn(self.ci3, cs)
        self.assertNotIn(self.ci4, cs)
        self.assertNotIn(self.ci5, cs)
        self.assertNotIn(self.ci6, cs)
        self.assertNotIn(self.ci7, cs)
        self.assertNotIn(self.ci8, cs)

    def test_no_perms_get_self_u3(self):  # always get self.
        cs = Invoice.objects.visible_to(self.user3)
        self.assertNotIn(self.ci1, cs)
        self.assertNotIn(self.ci2, cs)
        self.assertNotIn(self.ci3, cs)
        self.assertNotIn(self.ci4, cs)
        self.assertIn(self.ci5, cs)
        self.assertNotIn(self.ci6, cs)
        self.assertIn(self.ci7, cs)
        self.assertNotIn(self.ci8, cs)

    def test_no_perms_get_self_in_alliance(self):
        cs = Invoice.objects.visible_to(self.user2)
        self.assertNotIn(self.ci1, cs)
        self.assertNotIn(self.ci2, cs)
        self.assertIn(self.ci3, cs)
        self.assertNotIn(self.ci4, cs)
        self.assertNotIn(self.ci5, cs)
        self.assertNotIn(self.ci6, cs)
        self.assertNotIn(self.ci7, cs)
        self.assertNotIn(self.ci8, cs)

    def test_get_corp_in_alliance(self):
        self.user2.user_permissions.add(self.view_corp_permission)
        cs = Invoice.objects.visible_to(self.user2)
        self.assertNotIn(self.ci1, cs)
        self.assertNotIn(self.ci2, cs)
        self.assertIn(self.ci3, cs)
        self.assertIn(self.ci4, cs)
        self.assertNotIn(self.ci5, cs)
        self.assertNotIn(self.ci6, cs)
        self.assertNotIn(self.ci7, cs)
        self.assertNotIn(self.ci8, cs)

    def test_get_alliance_no_alliance(self):
        self.user4.user_permissions.add(self.view_alliance_permission)
        cs = Invoice.objects.visible_to(self.user4)
        self.assertNotIn(self.ci1, cs)
        self.assertNotIn(self.ci2, cs)
        self.assertNotIn(self.ci3, cs)
        self.assertNotIn(self.ci4, cs)
        self.assertNotIn(self.ci5, cs)
        self.assertNotIn(self.ci6, cs)
        self.assertIn(self.ci7, cs)
        self.assertNotIn(self.ci8, cs)
        self.assertIn(self.ci9, cs)

    def test_get_alliance(self):
        self.user3.user_permissions.add(self.view_alliance_permission)
        cs = Invoice.objects.visible_to(self.user3)
        self.assertNotIn(self.ci1, cs)
        self.assertNotIn(self.ci2, cs)
        self.assertNotIn(self.ci3, cs)
        self.assertNotIn(self.ci4, cs)
        self.assertIn(self.ci5, cs)
        self.assertIn(self.ci6, cs)
        self.assertIn(self.ci7, cs)
        self.assertNotIn(self.ci8, cs)

    def test_get_alliance_with_corp(self):
        self.user3.user_permissions.add(self.view_alliance_permission)
        self.user3.user_permissions.add(self.view_corp_permission)
        cs = Invoice.objects.visible_to(self.user3)
        self.assertNotIn(self.ci1, cs)
        self.assertNotIn(self.ci2, cs)
        self.assertNotIn(self.ci3, cs)
        self.assertNotIn(self.ci4, cs)
        self.assertIn(self.ci5, cs)
        self.assertIn(self.ci6, cs)
        self.assertIn(self.ci7, cs)
        self.assertNotIn(self.ci8, cs)

    def test_global_perms_u1(self):
        self.user3.user_permissions.add(self.view_all_permission)
        cs = Invoice.objects.visible_to(self.user3)
        self.assertIn(self.ci1, cs)
        self.assertIn(self.ci2, cs)
        self.assertIn(self.ci3, cs)
        self.assertIn(self.ci4, cs)
        self.assertIn(self.ci5, cs)
        self.assertIn(self.ci6, cs)
        self.assertIn(self.ci7, cs)
        self.assertIn(self.ci8, cs)

    def test_global_perms_u2(self):
        self.user2.user_permissions.add(self.view_all_permission)
        cs = Invoice.objects.visible_to(self.user2)
        self.assertIn(self.ci1, cs)
        self.assertIn(self.ci2, cs)
        self.assertIn(self.ci3, cs)
        self.assertIn(self.ci4, cs)
        self.assertIn(self.ci5, cs)
        self.assertIn(self.ci6, cs)
        self.assertIn(self.ci7, cs)
        self.assertIn(self.ci8, cs)

    def test_global_perms_u3(self):
        self.user2.user_permissions.add(self.view_all_permission)
        cs = Invoice.objects.visible_to(self.user2)
        self.assertIn(self.ci1, cs)
        self.assertIn(self.ci2, cs)
        self.assertIn(self.ci3, cs)
        self.assertIn(self.ci4, cs)
        self.assertIn(self.ci5, cs)
        self.assertIn(self.ci6, cs)
        self.assertIn(self.ci7, cs)
        self.assertIn(self.ci8, cs)

    def test_no_su_perms(self):
        cs = Invoice.objects.visible_to(self.user5)
        self.assertNotIn(self.ci1, cs)
        self.assertNotIn(self.ci2, cs)
        self.assertNotIn(self.ci3, cs)
        self.assertNotIn(self.ci4, cs)
        self.assertNotIn(self.ci5, cs)
        self.assertNotIn(self.ci6, cs)
        self.assertNotIn(self.ci7, cs)
        self.assertNotIn(self.ci8, cs)

        self.user5.is_superuser=True
        
        cs = Invoice.objects.visible_to(self.user5)
        self.assertIn(self.ci1, cs)
        self.assertIn(self.ci2, cs)
        self.assertIn(self.ci3, cs)
        self.assertIn(self.ci4, cs)
        self.assertIn(self.ci5, cs)
        self.assertIn(self.ci6, cs)
        self.assertIn(self.ci7, cs)
        self.assertIn(self.ci8, cs)
