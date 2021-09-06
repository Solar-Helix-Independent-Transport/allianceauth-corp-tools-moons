import os
import datetime

from django.db.models import Sum
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from .models import MoonFrack, MiningObservation, InvoiceRecord
from corptools.models import EveLocation
from django.core.exceptions import PermissionDenied

@login_required
def extractions(request):
    if request.user.has_perm('moons.view_available'):
        days_to_hold = timezone.now() - datetime.timedelta(days=3)

        events = MoonFrack.objects.visible_to(request.user)
        future_fracks = events.filter(arrival_time__gt=timezone.now())
        current_fracks = events.filter(arrival_time__gte=days_to_hold, arrival_time__lt=timezone.now())
        
    else:
        raise PermissionDenied('You do not have permission to be here. This has been Logged!')

    context = {
        'events': future_fracks,
        'current_fracks': current_fracks,
    }

    return render(request, 'moons/list.html', context=context)


@login_required
@permission_required("admin")
def observers(request):
    all_obs=MiningObservation.objects.all().values('structure').distinct()
    locations = EveLocation.objects.filter(location_id__in=all_obs)
        
    context = {
        'observers': locations,
    }

    return render(request, 'moons/observers.html', context=context)


@login_required
@permission_required("admin")
def observer(request, observer_id):
    MiningObservation.objects.filter(observing_id=observer_id)

    context = {
        'observations': obs,
    }

    return render(request, 'moons/observers.html', context=context)



