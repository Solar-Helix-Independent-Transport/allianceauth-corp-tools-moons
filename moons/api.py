from allianceauth.eveonline.models import EveCharacter
from datetime import timedelta

from typing import List
from django.utils import timezone
from django.utils.timezone import activate

from ninja import NinjaAPI, Form, main
from ninja.security import django_auth
from ninja.responses import codes_4xx

from django.core.exceptions import PermissionDenied
from django.db.models import F, Sum, Q
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from django.conf import settings

from . import models
from corptools.models import MapSystemMoon
from . import schema

from django.db.models import Sum

import logging

logger = logging.getLogger(__name__)


api = NinjaAPI(title="MoonTool API", version="0.0.1",
               urls_namespace='moons:api', auth=django_auth, csrf=True,
               openapi_url=settings.DEBUG and "/openapi.json" or "")


@api.get(
    "/user/permisions",
    response={200: schema.MoonPermisions},
    tags=["User"]
)
def get_user_permisions(request, search_text: str):
    return []


@api.get(
    "/moon/search",
    response={200: List[schema.IdName]},
    tags=["Moons"]
)
def get_moon_search(request, search_text: str):
    return MapSystemMoon.objects.filter(name__icontains=search_text).values("name", id=F("moon_id"))


@api.get(
    "/character/search",
    response={200: List[schema.Character]},
    tags=["Character"]
)
def get_character_search(request, search_text: str):
    return EveCharacter.objects.filter(character_name__icontains=search_text)


@api.get(
    "/extraction/active",
    response={200: List[schema.ExtractionEvent]},
    tags=["Observers"]
)
def get_observer_usage(request, observer_id: int):
    if not request.user.has_perm("moons.access_moons"):
        return []
    time_from = timezone.now() - timedelta(days=6)
    observations = models.MiningObservation.objects \
        .filter(observing_id=observer_id, last_updated__gte=time_from) \
        .values('type_id') \
        .annotate(mined=(Sum('quantity') * F('type_name__volume'))) \
        .annotate(name=F('type_name__name'))

    return observations


@api.get(
    "/extraction/remaining",
    response={200: List[schema.OreVolume]},
    tags=["Observers"]
)
def get_observer_usage(request, observer_id: int):
    if not request.user.has_perm("moons.access_moons"):
        return []
    time_from = timezone.now() - timedelta(days=6)
    observations = models.MiningObservation.objects \
        .filter(observing_id=observer_id, last_updated__gte=time_from) \
        .values('type_id') \
        .annotate(mined=(Sum('quantity') * F('type_name__volume'))) \
        .annotate(name=F('type_name__name'))

    return observations


logger = logging.getLogger(__name__)


api = NinjaAPI(title="MoonTool API", version="0.0.1",
               urls_namespace='moons:api', auth=django_auth, csrf=True,
               openapi_url=settings.DEBUG and "/openapi.json" or "")


@api.get(
    "/user/permisions",
    response={200: schema.MoonPermisions},
    tags=["User"]
)
def get_user_permisions(request, search_text: str):
    return []


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
    "/extraction/active",
    response={200: List[schema.ExtractionEvent]},
    tags=["Observers"]
)
def get_observer_usage(request, observer_id: int):
    if not request.user.has_perm("moons.access_moons"):
        return []
    time_from = timezone.now() - timedelta(days=6)
    observations = models.MiningObservation.objects \
        .filter(observing_id=observer_id, last_updated__gte=time_from) \
        .values('type_id') \
        .annotate(mined=(Sum('quantity') * F('type_name__volume'))) \
        .annotate(name=F('type_name__name'))

    return observations


@api.get(
    "/rental/list",
    response={200: List[schema.MoonRenatal]},
    tags=["Rentals"]
)
def get_moon_rentals(request):
    if not request.user.has_perm("moons.access_moons"):
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


@api.post(
    "/rental/new",
    response={200: schema.MoonRenatal, 403: str},
    tags=["Rentals"]
)
def post_moon_rental_new(request, rental: schema.NewMoonRenatal = Form(...)):
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
