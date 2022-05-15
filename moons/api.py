from allianceauth.eveonline.models import EveCharacter
from datetime import timedelta

from typing import List
from django.utils import timezone
from django.utils.timezone import activate
from moons.helpers import OreHelper, what_frack_id

from ninja import NinjaAPI, Form, main
from ninja.security import django_auth
from ninja.responses import codes_4xx

from django.core.exceptions import PermissionDenied
from django.db.models import F, Sum, Q, Max, Min
from django.db.models import Subquery, OuterRef
from django.db.models import FloatField, F, ExpressionWrapper

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from django.conf import settings
from esi.models import Token

from . import models
from corptools.models import CharacterAudit, CorporationAudit, MapSystemMoon
from . import schema

from invoices.models import Invoice

from django.db.models import Sum

import logging

logger = logging.getLogger(__name__)


api = NinjaAPI(title="MoonTool API", version="0.0.1",
               urls_namespace='moons:api', auth=django_auth, csrf=True,
               openapi_url=settings.DEBUG and "/openapi.json" or "")


@api.get(
    "/user/permissions",
    response={200: schema.MoonPermisions},
    tags=["User"]
)
def get_user_permisions(request):
    return {
        "view_public_extractions": request.user.has_perm('moons.view_available'),
        "view_corp_extractions": request.user.has_perm('moons.view_corp'),
        "view_alliance_extractions": request.user.has_perm('moons.view_alliance'),
        "view_observations": request.user.has_perm('moons.view_all'),
        "view_rentals": request.user.has_perm('moons.view_moonrental'),
        "edit_rentals": request.user.has_perm('moons.change_moonrental'),
        "su": request.user.is_superuser
    }


JACKPOT_IDS = [
    46281,  # Glistening Zeolites
    46283,  # Glistening Sylvite
    46285,  # Glistening Bitumens
    46287,  # Glistening Coesite
    46305,  # Glowing Carnotite
    46307,  # Glowing Zircon
    46309,  # Glowing Pollucite
    46311,  # Glowing Cinnabar
    46297,  # Shimmering Otavite
    46299,  # Shimmering Sperrylite
    46301,  # Shimmering Vanadinite
    46303,  # Shimmering Chromite
    46289,  # Twinkling Cobaltite
    46291,  # Twinkling Euxenite
    46293,  # Twinkling Titanite
    46295,  # Twinkling Scheelite
    46313,  # Shining Xenotime
    46315,  # Shining Monazite
    46317,  # Shining Loparite
    46319,  # Shining Ytterbite
]


@api.get(
    "/extractions/",
    response={200: List[schema.ExtractionEvent]},
    tags=["Observers"]
)
def get_moons_and_obs(request):
    if not request.user.has_perm("moons.view_available"):
        return []
    past_days = 3

    return get_moons_and_extractions(request, past_days)


"""
    start_date = timezone.now() - timedelta(days=past_days)
    time_from = timezone.now() - timedelta(days=past_days+1)

    events = models.MoonFrack.objects.visible_to(request.user)
    current_fracks = events.filter(
        arrival_time__gte=start_date,
        arrival_time__lt=timezone.now()).select_related(
            "moon_name",
            "moon_name__system",
            "moon_name__system__constellation",
            "moon_name__system__constellation__region",
    ).prefetch_related('frack',
                       "frack__ore",
                       "frack__ore__group"
                       )

    type_price = models.OrePrice.objects.filter(item_id=OuterRef('type_id'))

    output = {}
    str_ob_dict = {}

    for e in current_fracks:
        output[e.structure_id] = {
            "ObserverName": e.structure.location_name,
            "system": e.moon_name.system.name,
            "constellation": e.moon_name.system.constellation.name,
            "region": e.moon_name.system.constellation.region.name,
            "moon": {
                "name": e.moon_name.name,
                "id": e.moon_id
            },
            "extraction_end": e.arrival_time,
            "mined_ore": [],
            "total_m3": 0,
            "value": 0

        }
        for o in e.frack.all():
            if e.structure_id not in str_ob_dict:
                str_ob_dict[e.structure_id] = {}
            output[e.structure_id]['total_m3'] += o.total_m3
            str_ob_dict[e.structure_id][o.ore.name] = {
                "type": {
                    "id": o.ore_id,
                    "name": o.ore.name,
                    "cat": o.ore.group.name,
                    "cat_id": o.ore.group_id
                },
                "volume": 0,
                "total_volume": o.total_m3,
                "value": 0
            }

    observations = models.MiningObservation.objects \
        .filter(last_updated__gte=time_from) \
        .filter(observing_id__in=current_fracks.values_list("structure_id", flat=True)) \
        .values('structure', 'type_id') \
        .annotate(mined=(Sum('quantity') * F('type_name__volume'))) \
        .annotate(ore_value=ExpressionWrapper(
            Subquery(type_price.values('price')) * Sum('quantity'),
            output_field=FloatField())) \
        .annotate(name=F('type_name__name'))

    for o in observations:
        nme = o["name"].split(" ")[-1]
        if request.user.has_perm("moons.view_all"):
            str_ob_dict[o["structure"]][nme]["value"] += o["ore_value"]
        str_ob_dict[o["structure"]][nme]["volume"] += o['mined']

        if o['type_id'] in JACKPOT_IDS:
            output[o["structure"]]["jackpot"] = True

    for s, o in str_ob_dict.items():
        output[s]["mined_ore"] = list(o.values())

    return list(output.values())
"""


@api.get(
    "/extractions/past",
    response={200: List[schema.ExtractionEvent]},
    tags=["Observers"]
)
def get_moons_and_obs_past(request):
    if not request.user.has_perm("moons.view_all"):
        return []

    past_days = 30*12  # 12 months = max pull 6 events per moon

    return get_moons_and_extractions(request, past_days)


def get_moons_and_extractions(request, past_days):
    start_date = timezone.now() - timedelta(days=past_days)
    time_from = timezone.now() - timedelta(days=past_days+1)

    events = models.MoonFrack.objects.visible_to(request.user)
    current_fracks = events.filter(
        arrival_time__gte=start_date,
        arrival_time__lt=timezone.now()).select_related(
            "moon_name",
            "moon_name__system",
            "moon_name__system__constellation",
            "moon_name__system__constellation__region",
    ).prefetch_related('frack',
                       "frack__ore",
                       "frack__ore__group"
                       )

    type_price = models.OrePrice.objects.filter(item_id=OuterRef('type_id'))

    output = {}
    str_ob_dict = {}

    for e in current_fracks:
        output[e.id] = {
            "ObserverName": e.structure.location_name,
            "system": e.moon_name.system.name,
            "constellation": e.moon_name.system.constellation.name,
            "region": e.moon_name.system.constellation.region.name,
            "moon": {
                "name": e.moon_name.name,
                "id": e.moon_id
            },
            "extraction_end": e.arrival_time,
            "extraction_end": e.arrival_time,
            "mined_ore": [],
            "total_m3": 0,
            "value": 0,
            "structure_id": e.structure.location_id
        }

        for o in e.frack.all():
            if e.id not in str_ob_dict:
                str_ob_dict[e.id] = {}
            output[e.id]['total_m3'] += o.total_m3
            str_ob_dict[e.id][o.ore.name] = {
                "type": {
                    "id": o.ore_id,
                    "name": o.ore.name,
                    "cat": o.ore.group.name,
                    "cat_id": o.ore.group_id
                },
                "volume": 0,
                "total_volume": o.total_m3,
                "value": 0
            }

    observations = models.MiningObservation.objects \
        .filter(last_updated__gte=time_from) \
        .filter(observing_id__in=current_fracks.values_list("structure_id", flat=True)) \
        .values('structure', 'type_id', "last_updated") \
        .annotate(mined=(Sum('quantity') * F('type_name__volume'))) \
        .annotate(ore_value=ExpressionWrapper(
            Subquery(type_price.values('price')) * Sum('quantity'),
            output_field=FloatField())) \
        .annotate(name=F('type_name__name'))

    for o in observations:
        frack = what_frack_id(output, o)
        if frack == False:
            continue
        nme = o["name"].split(" ")[-1]
        if frack in str_ob_dict:
            if request.user.has_perm("moons.view_all"):
                str_ob_dict[frack][nme]["value"] += o["ore_value"]
                output[frack]['value'] += o["ore_value"]
            str_ob_dict[frack][nme]["volume"] += o['mined']

        if o['type_id'] in JACKPOT_IDS:
            output[frack]["jackpot"] = True

    for s, o in str_ob_dict.items():
        output[s]["mined_ore"] = list(o.values())

    return list(output.values())


@api.get(
    "/extractions/future",
    response={200: List[schema.ExtractionEvent]},
    tags=["Observers"]
)
def get_future_extractions(request):
    if not request.user.has_perm("moons.view_all"):
        return []

    start_date = timezone.now()

    events = models.MoonFrack.objects.visible_to(request.user)
    current_fracks = events.filter(
        arrival_time__gte=start_date).select_related(
            "moon_name",
            "moon_name__system",
            "moon_name__system__constellation",
            "moon_name__system__constellation__region",
    ).prefetch_related('frack',
                       "frack__ore",
                       "frack__ore__group"
                       )

    type_prices = OreHelper.get_ore_array_with_value()

    output = {}
    str_ob_dict = {}

    for e in current_fracks:
        output[e.structure_id] = {
            "ObserverName": e.structure.location_name,
            "system": e.moon_name.system.name,
            "constellation": e.moon_name.system.constellation.name,
            "region": e.moon_name.system.constellation.region.name,
            "moon": {
                "name": e.moon_name.name,
                "id": e.moon_id
            },
            "extraction_end": e.arrival_time,
            "mined_ore": [],
            "total_m3": 0,
            "value": 0
        }
        for o in e.frack.all():
            value = int(float(
                o.total_m3) / float(type_prices[o.ore_id]["volume"]) * float(type_prices[o.ore_id]["value"]))
            if e.structure_id not in str_ob_dict:
                str_ob_dict[e.structure_id] = {}
            output[e.structure_id]['total_m3'] += o.total_m3
            output[e.structure_id]['value'] += value

            str_ob_dict[e.structure_id][o.ore.name] = {
                "type": {
                    "id": o.ore_id,
                    "name": o.ore.name,
                    "cat": o.ore.group.name,
                    "cat_id": o.ore.group_id
                },
                "volume": 0,
                "total_volume": o.total_m3,
                "value": value
            }

    for s, o in str_ob_dict.items():
        output[s]["mined_ore"] = list(o.values())

    return list(output.values())


@api.get(
    "/moons/search",
    response={200: List[schema.IdName]},
    tags=["Search"]
)
def get_moon_search(request, search_text: str, limit: int = 10):
    return MapSystemMoon.objects.filter(name__icontains=search_text).values("name", id=F("moon_id"))[:limit]


@api.get(
    "/corporations/search",
    response={200: List[schema.Corporation]},
    tags=["Search"]
)
def get_corporation_search(request, search_text: str, limit: int = 10):
    return EveCorporationInfo.objects.filter(corporation_name__icontains=search_text)[:limit]


@api.get(
    "/characters/search",
    response={200: List[schema.Character]},
    tags=["Search"]
)
def get_character_search(request, search_text: str, limit: int = 10):
    return EveCharacter.objects.filter(character_name__icontains=search_text)[:limit]


@api.get(
    "/rental/list",
    response={200: List[schema.MoonRental]},
    tags=["Rentals"]
)
def get_moon_rentals(request):
    if not request.user.has_perm("moons.add_moonrental"):
        return []

    rentals = models.MoonRental.objects.filter(end_date__isnull=True).select_related(
        "moon", "moon__system", "contact", "corporation")
    out = []
    for r in rentals:
        out.append(
            {"moon": {
                "id": r.moon.moon_id,
                "name": r.moon.name
            },
                "system": {
                "id": r.moon.system.system_id,
                "name": r.moon.system.name
            },
                "contact": r.contact,
                "corporation": r.corporation,
                "price": r.price,
                "start_date": r.start_date
            }
        )

    return out


@api.get(
    "/rental/payments",
    response={200: List[schema.MoonRental]},
    tags=["Rentals"]
)
def get_moon_rental_payments(request):
    if not request.user.has_perm("moons.add_moonrental"):
        return []

    payments = Invoice.objects.filter(paid=False).select_related(
        "moon", "moon__system", "contact", "corporation")
    out = []
    for r in rentals:
        out.append(
            {"moon": {
                "id": r.moon.moon_id,
                "name": r.moon.name
            },
                "system": {
                "id": r.moon.system.system_id,
                "name": r.moon.system.name
            },
                "contact": r.contact,
                "corporation": r.corporation,
                "price": r.price,
                "start_date": r.start_date
            }
        )

    return out


@api.post(
    "/rental/new",
    response={200: schema.MoonRental, 403: str},
    tags=["Rentals"]
)
def post_moon_rental_new(request, rental: schema.NewMoonRental = Form(...)):
    if not request.user.has_perm("moons.add_moonrental"):
        return 403, "Permission Denied!"

    if models.MoonRental.objects.filter(moon_id=rental.moon_id, end_date__isnull=True).exists():
        return 403, "Moon Already Rented!"
    try:
        char = EveCharacter.objects.get(character_id=rental.contact_id)
    except EveCharacter.DoesNotExist:
        return 403, "Character Unknown to Auth"
    try:
        corp = EveCorporationInfo.objects.get(
            corporation_id=rental.corporation_id)
    except EveCorporationInfo.DoesNotExist:
        return 403, "Corporation Unknown to Auth"
    new_rental = models.MoonRental.objects.create(
        moon_id=rental.moon_id,
        contact=char,
        corporation=corp,
        price=rental.price,
        start_date=timezone.now()
    )
    return 200, {"moon": {
        "id": new_rental.moon.moon_id,
        "name": new_rental.moon.name
    },
        "system": {
        "id": new_rental.moon.system.system_id,
        "name": new_rental.moon.system.name
    },
        "contact": new_rental.contact,
        "corporation": new_rental.corporation,
        "price": new_rental.price,
        "start_date": new_rental.start_date
    }


@api.get(
    "/admin/list",
    response={200: List, 403: str},
    tags=["Admin"]
)
def get_corp_stats(request):
    if not request.user.is_superuser:
        return 403, "Permission Denied!"

    corps = CorporationAudit.objects.visible_to(request.user)

    output = []

    for c in corps:
        _c = {
            "name": c.corporation.corporation_name,
            "char_tokens": 0,
            "corp_tokens": 0,
            "obs": c.last_update_observers,
            "frack": "Never"
        }

        chars = CharacterAudit.objects.filter(character__corporation_id=c.corporation.corporation_id,
                                              characterroles__accountant=True,
                                              active=True)

        _c["char_tokens"] = chars.count()
        dt = chars.aggregate(Max("last_update_notif"))
        _c["frack"] = dt["last_update_notif__max"]
        scopes = ['esi-industry.read_corporation_mining.v1',
                  'esi-universe.read_structures.v1']

        tokens = Token.objects \
            .filter(character_id__in=chars.values_list("character__character_id", flat=True)) \
            .require_scopes(scopes)

        _c["corp_tokens"] = tokens.count()

        output.append(_c)

    return output
