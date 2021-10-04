import logging
import json
from datetime import timedelta, datetime
import yaml
import requests 

from celery import shared_task, chain
from django.utils import timezone
from . import app_settings
from .helpers import OreHelper
from .models import MiningObservation, MoonFrack, FrackOre, OrePrice, OreTaxRates, OreTax, InvoiceRecord
from corptools.models import Notification, EveLocation, MapSystemMoon, EveItemType, CorporationAudit, EveName
from corptools import providers
from corptools.task_helpers.corp_helpers import get_corp_token
from corptools.task_helpers.update_tasks import fetch_location_name
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
    notification_ids = set(fracks.values_list('notification__notification_id', flat=True))
    frack_dict = {}
    for frack in fracks:
        if frack.moon_id not in frack_dict:
            frack_dict[frack.moon_id] = {}
        frack_dict[frack.moon_id][frack.start_time] = frack

    _type_list = []
    _ores = []
    for notification in notifications:
        try:
            if notification.notification_id not in notification_ids:
                notification_ids.add(notification.notification_id)
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


@shared_task
def run_obs_for_all_corps(force=False):
    for c in CorporationAudit.objects.all():
        logger.debug(f"Sending Obs update for {c.corporation}")
        queue_moon_obs.apply_async(args=[c.corporation.corporation_id], priority=6)


@shared_task
def queue_moon_obs(corp_id, force=False):
    logger.debug("Started Mining Ob Sync for {}".format(corp_id))

    token = get_corp_token(corp_id, ['esi-industry.read_corporation_mining.v1'], ['Accountant', 'Director'])
    obs = providers.esi.client.Industry.get_corporation_corporation_id_mining_observers(corporation_id=corp_id,
                                                                                             token=token.valid_access_token()).results()
    task_queue = []
    for ob in obs:
        task_queue.append(process_moon_obs.si(ob.get('observer_id'), corp_id))
    chain(task_queue).apply_async(priority=8)


@shared_task
def process_moon_obs(observer_id, corporation_id):
    logger.debug("Started Mining Ob Sync for {}".format(observer_id))

    token = get_corp_token(corporation_id, ['esi-industry.read_corporation_mining.v1', 'esi-universe.read_structures.v1'], ['Accountant', 'Director'])
    obs = providers.esi.client.Industry.get_corporation_corporation_id_mining_observers_observer_id(corporation_id=corporation_id,
                                                                                                   observer_id=observer_id,
                                                                                                   token=token.valid_access_token()).results()
    eve_names = set(EveName.objects.all().values_list('eve_id', flat=True))
    type_names = set(EveItemType.objects.all().values_list('type_id', flat=True))
    corp = CorporationAudit.objects.get(corporation__corporation_id=corporation_id)

    observer = None
    structure_exists = False
    moon = None

    try:
        observer = EveLocation.objects.get(location_id=observer_id)
        structure_exists = True

    except EveLocation.DoesNotExist:
        _ob = fetch_location_name(observer_id, "solar_system", token.character_id)
        if _ob:
            _ob.save()
            observer = _ob
            structure_exists = True

    _moon = MoonFrack.objects.filter(structure_id=observer_id, moon_name__isnull=False)
    if _moon.exists():
        moon = _moon.last().moon_name

    ob_pks = set(MiningObservation.objects.filter(observing_id=observer_id).values_list('ob_pk', flat=True))
    mining_ob_updates = []
    mining_ob_creates = []
    new_eve_names = []
    new_item_types = []
    for ob in obs:
        pk = MiningObservation.build_pk(corporation_id, observer_id, ob.get('character_id'), ob.get('last_updated'), ob.get('type_id'))
        
        if ob.get('character_id') not in eve_names:
            new_eve_names.append(ob.get('character_id'))
            eve_names.add(ob.get('character_id'))

        if ob.get('type_id') not in type_names:
            new_item_types.append(ob.get('type_id'))
            type_names.add(ob.get('type_id'))

        _ob = MiningObservation(ob_pk=pk,
                                observing_id=observer_id,
                                observing_corporation=corp,
                                character_name_id=ob.get('character_id'),
                                character_id=ob.get('character_id'),
                                last_updated=ob.get('last_updated'),
                                quantity=ob.get('quantity'),
                                recorded_corporation_id=ob.get('recorded_corporation_id'),
                                type_id=ob.get('type_id'),
                                type_name_id=ob.get('type_id'),
                                moon=moon)

        if structure_exists:
            _ob.structure = observer

        if pk in ob_pks:
            mining_ob_updates.append(_ob)
        else: 
            mining_ob_creates.append(_ob)

    EveName.objects.create_bulk_from_esi(new_eve_names)
    EveItemType.objects.create_bulk_from_esi(new_item_types)

    if len(mining_ob_creates) > 0:
        MiningObservation.objects.bulk_create(mining_ob_creates)
    
    if len(mining_ob_updates) > 0:
        MiningObservation.objects.bulk_update(mining_ob_updates, ['quantity', 'last_updated', 'structure', 'observing_corporation'])

    msg = f"Corp:{corporation_id} Moon:{observer_id} Updated:{len(mining_ob_updates)} Created:{len(mining_ob_creates)}"
    logger.debug(msg)
    return msg


@shared_task
def update_ore_prices():
    mins = OreHelper.get_mineral_array()
    minstr = str(mins.pop())
    for i in mins:
        minstr += f",{i}"
    url = f"https://market.fuzzwork.co.uk/aggregates/?station=60003760&types={minstr}"
    response = requests.get(url)
    price_data = response.json()
    price_cache = {}
    for key, item in price_data.items():
        name, created = EveItemType.objects.get_or_create_from_esi(key)
        name = name.name
        if name not in price_cache:
            price_cache[name] = {}
        price_cache[name]['the_forge'] = float(item['buy']['weightedAverage'])

    ores = OreHelper.get_ore_array()

    price_source = 'the_forge'  # We only use this now.

    for ore, minerals in ores.items():
        price = 0
        for mineral, qty in minerals["minerals"].items():
            price = price + (qty * price_cache[mineral][price_source])

        OrePrice.objects.update_or_create(item=minerals['model'],
                                          defaults={
                                            "price": price/minerals['portion']
                                          })

    update_tax_prices.apply_async(priority=7)

    return json.dumps(price_cache)


@shared_task
def update_tax_prices():
    taxs = OreTaxRates.objects.all()

    ores = OreHelper.get_ore_array_with_value()

    for tax in taxs:
        for id, o in ores.items():
            rate = getattr(tax, o['rarity'])
            price = float(o['value']) * (float(rate)/100) * (float(tax.refine_rate)/100)
            OreTax.objects.update_or_create(
                item=o['model'],
                tax=tax,
                defaults={
                    "price": price
                }
            )


@shared_task
def generate_taxes():
    taxes = InvoiceRecord.generate_invoices()
    return f"Taxes Generated {taxes.base_ref} Total Mined:{taxes.total_mined:,} Total Tax:{taxes.total_taxed:,}"
