from django.db import models
from allianceauth.eveonline.models import EveCharacter
from allianceauth.notifications import notify
from corptools.models import CorporationAudit, EveLocation, EveItemType, MapSystemMoon, EveLocation, Notification, EveName

from . import app_settings
from .managers import MoonManager
from django.utils import timezone

from .managers import MoonManager
if app_settings.discord_bot_active():
    import aadiscordbot

import logging
logger = logging.getLogger(__name__)


class MoonFrack(models.Model):
    objects = MoonManager()

    corporation = models.ForeignKey(CorporationAudit, on_delete=models.CASCADE, related_name='moon')

    moon_name = models.ForeignKey(MapSystemMoon, on_delete=models.SET_NULL, null=True, default=None)
    moon_id = models.IntegerField()

    notification = models.ForeignKey(Notification, on_delete=models.SET_NULL, null=True, default=None)

    structure = models.ForeignKey(EveLocation, on_delete=models.CASCADE)

    start_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    auto_time = models.DateTimeField()

    class Meta:
        unique_together = (('arrival_time', 'moon_id'),)

    def __str__(self):
        return "{} - {}".format(self.moon_name.name, self.arrival_time)

    class Meta:
        permissions = (('view_available', 'Can View Configured Public Moons'),
                       ('view_corp', 'Can View Own Corps Moons'),  # these do nothing as of now.
                       ('view_alliance', 'Can View Own Alliances Moons'),
                       ('view_all', 'Can View All Moons'))

class FrackOre(models.Model):
    frack = models.ForeignKey(MoonFrack, on_delete=models.CASCADE, related_name='frack')
    ore = models.ForeignKey(EveItemType, on_delete=models.CASCADE)
    total_m3 = models.DecimalField(max_digits=20, decimal_places=2)

# Corp Mining Observation
class MiningObservation(models.Model):
    ob_pk = models.CharField(max_length=50, primary_key=True)

    observing_id = models.BigIntegerField(null=True, default=None, blank=True)
    character_name = models.ForeignKey(EveName, on_delete=models.SET_NULL, null=True, default=None)

    character_id = models.IntegerField()
    last_updated = models.DateTimeField()
    quantity = models.BigIntegerField()
    recorded_corporation_id = models.IntegerField()
    type_id = models.IntegerField()
    type_name = models.ForeignKey(EveItemType, on_delete=models.SET_NULL, null=True, default=None) 

    @classmethod
    def build_pk(cls, corp_id, observer_id, observed_character_id, ob_date):
        """
        Helper method to get a unique pk for a specific observation. Usefull for bulk updates of data.
        :param corp_id: Observer Corp.
        :param observer_id: Mining Observer ID.
        :param observed_character_id: Character Observed.
        :param ob_date: DateTime of observation.
        :return: :class:String
        """
        date_str = ob_date.strftime("%Y%m%d")
        return "{}-{}-{}-{}".format(char_id,
                                    observer_id,
                                    observed_character_id,
                                    date_str)

    class Meta:
        indexes = (
            models.Index(fields=['observing_id']),
            models.Index(fields=['last_updated']),
            models.Index(fields=['recorded_corporation_id']),
            models.Index(fields=['type_id']),
            models.Index(fields=['character_id'])
        )

