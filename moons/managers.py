from django.db import models
from django.core.exceptions import ObjectDoesNotExist
import logging

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo, EveAllianceInfo

logger = logging.getLogger(__name__)

class MoonQuerySet(models.QuerySet):
    def visible_to(self, user):
        # superusers get all visible
        if user.is_superuser:
            logger.debug('Returning all Moons for superuser %s.' % user)
            return self

        if user.has_perm('moons.view_all'):
            logger.debug('Returning all Moons for %s.' % user)
            return self

        try:
            char = user.profile.main_character
            assert char
            # build all accepted queries
            queries = []
            if user.has_perm('moons.view_alliance'):
                if char.alliance_id is not None:
                    queries.append(models.Q(corporation__corporation__alliance__alliance_id=char.alliance_id))
                else:
                    queries.append(models.Q(corporation__corporation__corporation_id=char.corporation_id))
            if user.has_perm('moons.view_corp'):
                if user.has_perm('moons.view_alliance'):
                    pass
                else:
                    queries.append(models.Q(corporation__corporation__corporation_id=char.corporation_id))
            logger.debug('%s queries for user %s characters.' % (len(queries), user))
            # filter based on queries
            query = queries.pop()
            for q in queries:
                query |= q
            return self.filter(query)
        except AssertionError:
            logger.debug('User %s has no main character. Nothing visible.' % user)
            return self.none()        


class MoonManager(models.Manager):

    def get_queryset(self):
        return MoonQuerySet(self.model, using=self._db)\
            .select_related('moon_name', 'corporation','corporation__corporation', 'structure', 'structure__system', 'structure__system__constellation')\
            .prefetch_related('frack', 'frack__ore')

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)
