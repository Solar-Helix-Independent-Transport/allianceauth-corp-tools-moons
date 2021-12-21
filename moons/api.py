from datetime import timedelta

from typing import List
from django.utils import timezone
from django.utils.timezone import activate

from ninja import NinjaAPI, Form, main
from ninja.security import django_auth
from ninja.responses import codes_4xx

from django.core.exceptions import PermissionDenied
from django.db.models import F, Sum, Q
from allianceauth.eveonline.models import EveCharacter
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
    "/moon/search",
    response={200: List[schema.MoonName]},
    tags=["Moons"]
)
def get_moon_search(request, search_text: str):
    return MapSystemMoon.objects.filter(name__icontains=search_text)


@api.get(
    "/character/search",
    response={200: List[schema.CharacterName]},
    tags=["Character"]
)
def get_character_search(request, search_text: str):
    return EveCharacter.objects.filter(character_name__icontains=search_text)


@api.get(
    "/extraction/remaining",
    response={200: List[schema.MinedOres]},
    tags=["Observers"]
)
def get_observer_usage(request, observer_id: int):
    if not request.user.has_perm("moons.access_moons"):
        return []
    time_from = timezone.now() - timedelta(days=6)
    observations = models.MiningObservation.objects \
        .filter(observing_id=observer_id, last_updated__gte=time_from) \
        .values('type_id') \
        .annotate(mined = (Sum('quantity') * F('type_name__volume'))) \
        .annotate(name=F('type_name__name'))

    return observations

