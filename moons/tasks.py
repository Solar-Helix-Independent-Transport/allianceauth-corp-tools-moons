import logging
import os 
from datetime import timedelta, datetime
import yaml

from celery import shared_task
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo, EveAllianceInfo
from django.utils import timezone
from . import app_settings
from .models import MiningObservation, MoonFrack, FrackOre
from corptools.models import Notification, EveLocation, MapSystemMoon, EveItemType, CorporationAudit
from corptools import providers
from corptools.task_helpers.corp_helpers import get_corp_token
from allianceauth.services.tasks import QueueOnce
from .app_settings import PUBLIC_MOON_CORPS

logger = logging.getLogger(__name__)

def filetime_to_dt(ft):
    us = (ft - 116444736000000000) // 10
    return datetime(1970, 1, 1) + timedelta(microseconds=us)

@shared_task
def process_moon_pulls():
    logger.debug("Started Mining Pull Sync")
    start_time = timezone.now() - timedelta(days=65)

    notification_type_filter = ['MoonminingExtractionStarted',]

    # YAML Structure
    #    autoTime: #####
    #    moonID: ####
    #    oreVolumeByType:
    #        45490: 3981232.1291307067
    #        45499: 7115599.461194293
    #        45504: 4589835.07632598
    #    readyTime: #####
    #    solarSystemID: ####
    #    startedBy: ####
    #    startedByLink: <a href="showinfo:1385//###">CCCC</a>
    #    structureID: ####
    #    structureLink: <a href="showinfo:35835//####">CCCC</a>
    #    structureName: CCCCCCCCC
    #    structureTypeID: ####

    notifications = Notification.objects.filter(character__character__corporation_id__in=PUBLIC_MOON_CORPS,
                                                timestamp__gte=start_time,
                                                notification_type__in=notification_type_filter)

    fracks = MoonFrack.objects.filter(start_time__gte=start_time)
    frack_dict = {}
    for frack in fracks:
        if frack.moon_id not in frack_dict:
            frack_dict[frack.moon_id] = {}
        frack_dict[frack.moon_id][frack.start_time] = frack

    _type_list = []
    _ores = []
    for notification in notifications:
        try:
            notification_data = yaml.load(notification.notification_text)
            moon_id = notification_data['moonID']
            start_time = notification.timestamp
        
            new_frack = False

            if moon_id in frack_dict:
                if start_time not in frack_dict[moon_id]:
                    new_frack = True
            else:
                new_frack = True
            
            if new_frack:
                _structure, _c = EveLocation.objects.update_or_create(location_id=notification_data['structureID'],
                                                                     defaults={
                                                                         "location_name":notification_data['structureName'],
                                                                         "system_id":notification_data['solarSystemID']
                                                                     })
                _moon, _c = MapSystemMoon.objects.get_or_create_from_esi(moon_id=moon_id)
                _corp_audit = CorporationAudit.objects.get(corporation__corporation_id=notification.character.character.corporation_id)
                _frack = MoonFrack.objects.create(corporation=_corp_audit,
                                                  moon_name=_moon,
                                                  moon_id=moon_id,
                                                  notification=notification,
                                                  structure=_structure,
                                                  start_time=start_time,
                                                  arrival_time=filetime_to_dt(notification_data['readyTime']),
                                                  auto_time=filetime_to_dt(notification_data['autoTime'])
                                                 )

                for ore, volume in notification_data['oreVolumeByType'].items():
                    if ore not in _type_list:
                        _type_list.append(ore)
                    _ores.append(FrackOre(frack=_frack,
                                          ore_id=ore,
                                          total_m3=volume
                                         ))
        except Exception as e:
            logger.warn("Failed to process moon", exc_info=1)
            pass

    EveItemType.objects.create_bulk_from_esi(_type_list)
    FrackOre.objects.bulk_create(_ores, batch_size=500)
    return "fetched!"


