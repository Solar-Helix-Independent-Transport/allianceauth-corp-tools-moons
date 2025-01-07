import datetime

from corptools.models import EveLocation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from moons.helpers import OreHelper

from . import __version__
from .api import get_moons_and_extractions
from .models import InvoiceRecord, MiningObservation, MoonFrack


@login_required
def extractions(request):
    if request.user.has_perm('moons.view_all'):
        days_to_hold = timezone.now() - datetime.timedelta(days=3)

        events = MoonFrack.objects.visible_to(request.user)
        future_fracks = events.filter(arrival_time__gt=timezone.now())
        current_fracks = events.filter(
            arrival_time__gte=days_to_hold, arrival_time__lt=timezone.now())

    else:
        raise PermissionDenied(
            'You do not have permission to be here. This has been Logged!')

    context = {
        'events': future_fracks,
        'current_fracks': current_fracks,
    }

    return render(request, 'moons/list.html', context=context)


@login_required
@permission_required("admin")
def observers(request):
    all_obs = MiningObservation.objects.all().values('structure').distinct()
    locations = EveLocation.objects.filter(location_id__in=all_obs)

    context = {
        'observers': locations,
    }

    return render(request, 'moons/observers.html', context=context)


@login_required
@permission_required("moons.view_available")
def react(request):
    context = {
        "version": __version__,
        "app_name": "moons",
        "page_title": "Moons"
    }

    return render(request, 'moons/react_base.html', context=context)


@login_required
def moon_report_use(request):
    if not request.user.has_perm('moons.view_all'):
        raise PermissionDenied("No perms to view")

    _ores = OreHelper.get_ore_array_with_value()
    fracks = get_moons_and_extractions(request, 365*10)

    output = []
    for frack in fracks:
        total_value_available = 0
        total_value = 0
        ores = []
        rank = 0
        for o in frack["mined_ore"]:
            total_value_available += \
                _ores[o["type"]["id"]]["value"] * (o["total_volume"]/10)
            total_value += o["value"]
            ores.append(o["type"]["name"])
            if o["type"]["cat_id"] > rank:
                rank = o["type"]["cat_id"]
        ratio = 0
        if total_value > 0:
            ratio = float(total_value)/float(total_value_available)*100
        _o = {
            "Corporation": frack["CorporationName"],
            "moon": frack["moon"]["name"],
            "end_date": frack["extraction_end"],
            "system": frack["system"],
            "constellation": frack["constellation"],
            "region": frack["region"],
            "total_value": total_value_available,
            "mined_value": total_value,
            "mined_ratio": ratio,
            "ores": ", ".join(ores),
            "rank": OreHelper.rank_ids[rank]
        }
        output.append(_o)

    context = {
        "fracks": output
    }

    return render(
        request,
        'moons/dashboards/moon_use_dash.html',
        context=context
    )
