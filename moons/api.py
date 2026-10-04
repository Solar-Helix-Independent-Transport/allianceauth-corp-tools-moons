import logging
from datetime import timedelta
from typing import List

from corptools.models import CharacterAudit, CorporationAudit
from eve_sde.models import Moon
# from invoices.models import Invoice
from ninja import Form, NinjaAPI
from ninja.security import django_auth

from django.conf import settings
from django.db.models import (
    Count, ExpressionWrapper, F, FloatField, OuterRef, Subquery, Sum,
)
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from esi.models import Token

from moons.helpers import OreHelper, what_frack_id

from . import app_settings, models, rent, scans, schema

logger = logging.getLogger(__name__)


api = NinjaAPI(title="MoonTool API", version="0.0.1",
               urls_namespace='moons:api', auth=django_auth,
               openapi_url=settings.DEBUG and "/openapi.json" or "")


@api.get(
    "/user/permissions",
    response={200: schema.MoonPermisions},
    tags=["User"]
)
def get_user_permissions(request):
    return {
        "view_public_extractions": request.user.has_perm('moons.view_available'),
        "view_corp_extractions": request.user.has_perm('moons.view_corp'),
        "view_alliance_extractions": request.user.has_perm('moons.view_alliance'),
        "view_limited_future": request.user.has_perm('moons.view_limited_future'),
        "view_observations": request.user.has_perm('moons.view_all'),
        "view_rentals": request.user.has_perm('moons.view_moonrental'),
        "edit_rentals": request.user.has_perm('moons.change_moonrental'),
        "add_rentals": request.user.has_perm('moons.add_moonrental'),
        "import_scans": request.user.has_perm('moons.add_moonscan'),
        "change_scans": request.user.has_perm('moons.change_moonscan'),
        "view_scans": request.user.has_perm('moons.view_moonscan'),
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


@api.get(
    "/extractions/past",
    response={200: List[schema.ExtractionEvent]},
    tags=["Observers"]
)
def get_moons_and_obs_past(request):
    if not request.user.has_perm("moons.view_all"):
        return []

    past_days = 30 * 12  # 12 months = max pull 6 events per moon

    return get_moons_and_extractions(request, past_days)


def get_moons_and_extractions(request, past_days):
    start_date = timezone.now() - timedelta(days=past_days)
    time_from = timezone.now() - timedelta(days=past_days + 1)

    events = models.MoonFrack.objects.visible_to(request.user)
    current_fracks = events.filter(
        arrival_time__gte=start_date,
        arrival_time__lt=timezone.now()
    ).select_related(
        "moon_name",
        "moon_name__solar_system",
        "moon_name__solar_system__constellation",
        "moon_name__solar_system__constellation__region",
    ).prefetch_related(
        'frack',
        "frack__ore",
        "frack__ore__group"
    )

    type_price = models.OrePrice.objects.filter(
        item_id=OuterRef('type_id'),
        goo_only=False
    )

    output = {}
    str_ob_dict = {}

    for e in current_fracks:
        output[e.id] = {
            "CorporationName": e.corporation.corporation.corporation_name,
            "ObserverName": e.structure.location_name,
            "system": e.moon_name.solar_system.name,
            "constellation": e.moon_name.solar_system.constellation.name,
            "region": e.moon_name.solar_system.constellation.region.name,
            "moon": {
                "name": e.moon_name.name,
                "id": e.moon_id
            },
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

    observations = models.MiningObservation.objects.filter(
        last_updated__gte=time_from
    ).filter(
        observing_id__in=current_fracks.values_list("structure_id", flat=True)
    ).values(
        'structure',
        'type_id',
        "last_updated"
    ).annotate(
        mined=(Sum('quantity') * F('type_name__volume'))
    ).annotate(
        ore_value=ExpressionWrapper(
            Subquery(type_price.values('price')) * Sum('quantity'),
            output_field=FloatField()
        )
    ).annotate(name=F('type_name__name'))

    for o in observations:
        frack = what_frack_id(output, o)
        if frack is False:
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
    perm_view_all = request.user.has_perm("moons.view_all")
    perm_view_limited = request.user.has_perm("moons.view_limited_future")
    if not (perm_view_all or perm_view_limited):
        return []

    start_date = timezone.now()

    events = models.MoonFrack.objects.visible_to(request.user)

    if perm_view_limited and not perm_view_all:
        end_time = timezone.now() + timedelta(days=app_settings.MOONS_LIMITED_FUTURE_DAYS)
        events = events.filter(
            arrival_time__lte=end_time,
            moon_name__system__constellation__region_id__in=app_settings.MOONS_LIMITED_FUTURE_REGIONS
        )

    current_fracks = events.filter(
        arrival_time__gte=start_date
    ).select_related(
            "moon_name",
            "moon_name__solar_system",
            "moon_name__solar_system__constellation",
            "moon_name__solar_system__constellation__region",
    ).prefetch_related(
        'frack',
        "frack__ore",
        "frack__ore__group"
    )

    type_prices = OreHelper.get_ore_array_with_value()

    output = {}
    str_ob_dict = {}

    for e in current_fracks:
        output[e.structure_id] = {
            "ObserverName": e.structure.location_name,
            "system": e.moon_name.solar_system.name,
            "constellation": e.moon_name.solar_system.constellation.name,
            "region": e.moon_name.solar_system.constellation.region.name,
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
            value = int(
                float(
                    o.total_m3
                ) / float(
                    type_prices[o.ore_id]["volume"]
                ) * float(
                    type_prices[o.ore_id]["value"]
                )
            )
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
    return Moon.objects.filter(name__icontains=search_text).values("name", "id")[:limit]


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
        "moon", "moon__solar_system", "moon__solar_system__constellation",
        "moon__solar_system__constellation__region", "contact", "corporation",
        "contact__character_ownership__user__profile__main_character", "reprice_method",
    )
    out = []
    for r in rentals:
        try:
            main_char = r.contact.character_ownership.user.profile.main_character
        except Exception:
            main_char = None
        out.append(
            {
                "id": r.id,
                "moon": {
                    "id": r.moon.id,
                    "name": r.moon.name
                },
                "system": {
                    "id": r.moon.solar_system.id,
                    "name": r.moon.solar_system.name
                },
                "constellation": r.moon.solar_system.constellation.name,
                "region": r.moon.solar_system.constellation.region.name,
                "contact": r.contact,
                "corporation": r.corporation,
                "main_character": main_char,
                "price": r.price,
                "start_date": r.start_date,
                "note": r.note,
                "reprice_method": r.reprice_method,
            }
        )

    return out


@api.get(
    "/rental/invalid",
    response={200: List[schema.MoonRental]},
    tags=["Rentals"]
)
def get_moon_rentals(request):
    if not request.user.has_perm("moons.add_moonrental"):
        return []

    rentals = models.MoonRental.objects.filter(
        end_date__isnull=True,
        contact__character_ownership=None
    ).select_related(
        "moon",
        "moon__solar_system",
        "moon__solar_system__constellation",
        "moon__solar_system__constellation__region",
        "contact",
        "corporation",
        "reprice_method",
    )
    out = []
    for r in rentals:
        out.append(
            {
                "id": r.id,
                "moon": {
                    "id": r.moon.id,
                    "name": r.moon.name
                },
                "system": {
                    "id": r.moon.solar_system.id,
                    "name": r.moon.solar_system.name
                },
                "constellation": r.moon.solar_system.constellation.name,
                "region": r.moon.solar_system.constellation.region.name,
                "contact": r.contact,
                "corporation": r.corporation,
                "price": r.price,
                "start_date": r.start_date,
                "note": r.note,
                "reprice_method": r.reprice_method,
            }
        )

    return out


# @api.get(
#     "/rental/payments",
#     response={200: List[schema.MoonRental]},
#     tags=["Rentals"]
# )
# def get_moon_rental_payments(request):
#     if not request.user.has_perm("moons.add_moonrental"):
#         return []

#     payments = Invoice.objects.filter(paid=False).select_related(
#         "moon", "moon__system", "contact", "corporation")
#     out = []
#     for r in rentals:
#         out.append(
#             {"moon": {
#                 "id": r.moon.moon_id,
#                 "name": r.moon.name
#             },
#                 "system": {
#                 "id": r.moon.system.system_id,
#                 "name": r.moon.system.name
#             },
#                 "contact": r.contact,
#                 "corporation": r.corporation,
#                 "price": r.price,
#                 "start_date": r.start_date
#             }
#         )

#     return out


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
    if rental.reprice_method_id and not models.OreTaxRates.objects.filter(id=rental.reprice_method_id).exists():
        return 403, "Unknown reprice method"
    new_rental = models.MoonRental.objects.create(
        reprice_method_id=rental.reprice_method_id,
        moon_id=rental.moon_id,
        contact=char,
        corporation=corp,
        price=rental.price,
        note=rental.note,
        start_date=timezone.now()
    )
    return 200, {"id": new_rental.id, "moon": {
        "id": new_rental.moon.id,
        "name": new_rental.moon.name
    },
        "system": {
        "id": new_rental.moon.solar_system.id,
        "name": new_rental.moon.solar_system.name
    },
        "constellation": new_rental.moon.solar_system.constellation.name,
        "region": new_rental.moon.solar_system.constellation.region.name,
        "contact": new_rental.contact,
        "corporation": new_rental.corporation,
        "price": new_rental.price,
        "start_date": new_rental.start_date,
        "note": new_rental.note,
        "reprice_method": new_rental.reprice_method,
    }


@api.post(
    "/rental/{rental_id}/reprice_method",
    response={200: str, 400: str, 403: str, 404: str},
    tags=["Rentals"]
)
def post_moon_rental_reprice_method(request, rental_id: int, body: schema.SetRepriceMethod = Form(...)):
    """Pick the ore tax the reprice_rentals task prices this rental under, or none to leave it alone."""
    if not request.user.has_perm("moons.change_moonrental"):
        return 403, "Permission Denied!"
    rental = models.MoonRental.objects.filter(id=rental_id, end_date__isnull=True).select_related("moon").first()
    if not rental:
        return 404, "No active rental found."
    method = None
    if body.reprice_method_id:
        method = models.OreTaxRates.objects.filter(id=body.reprice_method_id).first()
        if not method:
            return 400, "Unknown reprice method"
    rental.reprice_method = method
    rental.save(update_fields=["reprice_method"])
    logger.info(f"{request.user} set {rental.moon.name} reprice method to {method or 'none'}")
    return 200, f"{rental.moon.name} {'reprices with ' + method.tag if method else 'is not repriced'}"


@api.post(
    "/rental/{rental_id}/end",
    response={200: str, 400: str, 403: str, 404: str},
    tags=["Rentals"]
)
def post_moon_rental_end(request, rental_id: int, body: schema.EndMoonRental = Form(...)):
    # same permission and note trail as the Discord unrent command
    if not request.user.has_perm("moons.change_moonrental"):
        return 403, "Permission Denied!"
    note = body.note.strip()
    if not note:
        return 400, "A note is required to unrent a moon."
    rental = models.MoonRental.objects.filter(id=rental_id, end_date__isnull=True).select_related("moon").first()
    if not rental:
        return 404, "No active rental found."
    try:
        who = request.user.profile.main_character.character_name
    except AttributeError:
        who = request.user.username
    rental.end_date = timezone.now()
    rental.note += f"\nUnrented, completed by {who}: {note}"
    rental.save()
    logger.info(f"{request.user} unrented {rental.moon.name}: {note}")
    return 200, f"Unrented {rental.moon.name}"


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

    scopes = ['esi-industry.read_corporation_mining.v1',
              'esi-universe.read_structures.v1']

    for c in corps:
        chars = list(
            CharacterAudit.objects.filter(
                character__corporation_id=c.corporation.corporation_id,
                characterroles__accountant=True,
                active=True
            ).select_related('character')
        )

        tokens = Token.objects \
            .filter(character_id__in=[ca.character.character_id for ca in chars]) \
            .require_scopes(scopes)

        output.append({
            "name": c.corporation.corporation_name,
            "char_tokens": len(chars),
            "corp_tokens": tokens.count(),
            "obs": c.get_update_time('observers'),
            "frack": c.get_update_time('moons'),
        })

    return output


@api.get(
    "/admin/explain",
    response={200: dict, 403: str},
    tags=["Admin"]
)
def get_explain_tax(request):
    if not request.user.is_superuser:
        return 403, "Permission Denied!"
    last_date = models.InvoiceRecord.get_last_invoice_date()
    data = models.MiningObservation.explain_taxes(last_date, timezone.now())
    return data


@api.get(
    "/admin/outstanding",
    response={200: list, 403: str},
    tags=["Admin"]
)
def get_outstanding_tax(request):
    if not request.user.is_superuser:
        return 403, "Permission Denied!"
    output = []
    last_date = models.InvoiceRecord.get_last_invoice_date()
    output.append(f"Last Invoice {last_date}!")
    locations = set()
    data = models.InvoiceRecord.generate_invoice_data()
    total_mined = 0
    total_taxed = 0
    # run known people
    for u, d in data['knowns'].items():
        try:
            total_mined += d['total_value']
            total_taxed += d['tax_value']
            for loc in d['locations']:
                locations.add(loc)
        except KeyError:
            pass  # probably wanna ping admin about it.

    for u, d in data['unknowns'].items():
        try:
            total_mined += d['totals_isk']
            total_taxed += d['tax_isk']
            for loc in d['seen_at']:
                locations.add(loc)
        except KeyError:
            pass  # probably wanna ping admin about it.

    output.append(
        f"We've seen {len(data['knowns'])} known members!"
    )
    output.append(
        f"We've seen { len(data['unknowns']) } unknown characters!"
    )
    output.append(
        f"Who have mined ${total_mined:,} worth of ore!"
    )
    output.append(
        f"Current Tax puts this at ${total_taxed:,} in taxes!\n"
    )
    output.append(
        "the structures included are:"
    )

    for s in locations:
        output.append(f"  - {s}")

    return output


def _scan_results(results):
    out = []
    for r in results:
        ores = [
            {
                "type_id": type_id,
                "name": r.ore_names.get(type_id),
                "fraction": r.ores.get(type_id),
                "previous": r.previous.get(type_id),
            }
            for type_id in sorted({*r.ores, *r.previous})
        ]
        out.append({
            "moon_id": r.moon_id, "name": r.name, "status": r.status,
            "reason": r.reason, "flagged": r.flagged, "ores": ores,
        })
    return out


@api.post(
    "/scans/preview",
    response={200: List[schema.ScanImportResult], 403: str},
    tags=["Scans"]
)
def post_scan_preview(request, body: schema.ScanText):
    if not request.user.has_perm("moons.add_moonscan"):
        return 403, "Permission Denied!"
    return 200, _scan_results(scans.preview_import(body.text, request.user))


@api.post(
    "/scans/import",
    response={200: List[schema.ScanImportResult], 403: str},
    tags=["Scans"]
)
def post_scan_import(request, body: schema.ScanText):
    if not request.user.has_perm("moons.add_moonscan"):
        return 403, "Permission Denied!"
    results = scans.commit_import(body.text, request.user)
    logger.info(f"{request.user} imported moon scans: "
                f"{sum(r.status in (scans.NEW, scans.CHANGED) for r in results)} written")
    return 200, _scan_results(results)


def _can_see_rental_suggestions(user):
    return user.has_perm("moons.add_moonrental") or user.has_perm("moons.change_moonrental")


@api.get(
    "/scans/profiles",
    response={200: List[schema.TaxProfile], 403: str},
    tags=["Scans"]
)
def get_scan_profiles(request):
    # rental admins pick a profile for price suggestions without needing scan access
    if not (request.user.has_perm("moons.view_moonscan")
            or _can_see_rental_suggestions(request.user)):
        return 403, "Permission Denied!"
    return 200, models.OreTaxRates.objects.filter(show_in_moon_values=True).order_by("id")


@api.get(
    "/scans/regions",
    response={200: List[schema.ScannedRegion], 403: str},
    tags=["Scans"]
)
def get_scanned_regions(request):
    if not request.user.has_perm("moons.view_moonscan"):
        return 403, "Permission Denied!"
    region = "moon__solar_system__constellation__region"
    return 200, [
        {"id": r[f"{region}_id"], "name": r[f"{region}__name"], "moons": r["moons"]}
        for r in models.MoonScan.objects.values(f"{region}_id", f"{region}__name")
        .annotate(moons=Count("id")).order_by(f"{region}__name")
    ]


def _can_see_scan_coverage(user):
    return user.has_perm("moons.add_moonscan") or user.has_perm("moons.view_moonscan")


@api.get(
    "/scans/coverage",
    response={200: List[schema.RegionCoverage], 403: str},
    tags=["Scans"]
)
def get_scan_coverage(request):
    """Every region with moons: how many it has and how many are scanned."""
    if not _can_see_scan_coverage(request.user):
        return 403, "Permission Denied!"
    region = "solar_system__constellation__region"
    scanned = dict(
        models.MoonScan.objects.values(f"moon__{region}_id")
        .annotate(n=Count("id")).values_list(f"moon__{region}_id", "n")
    )
    return 200, [
        {"id": r[f"{region}_id"], "name": r[f"{region}__name"], "moons": r["moons"],
         "scanned": scanned.get(r[f"{region}_id"], 0)}
        for r in Moon.objects.values(f"{region}_id", f"{region}__name")
        .annotate(moons=Count("id")).order_by(f"{region}__name")
    ]


@api.get(
    "/scans/coverage/{region_id}",
    response={200: List[schema.MissingMoon], 403: str},
    tags=["Scans"]
)
def get_missing_scans(request, region_id: int):
    """Moons in a region with no scan, by constellation, system, then moon."""
    if not _can_see_scan_coverage(request.user):
        return 403, "Permission Denied!"
    return 200, [
        {"id": moon_id, "name": name, "system": system, "constellation": constellation}
        for moon_id, name, system, constellation in Moon.objects.filter(
            solar_system__constellation__region_id=region_id, scan__isnull=True,
        ).order_by("solar_system__constellation__name", "solar_system__name", "id").values_list(
            "id", "name", "solar_system__name", "solar_system__constellation__name")
    ]


@api.get(
    "/scans/values",
    response={200: schema.ScannedMoonValues, 403: str, 404: str, 503: str},
    tags=["Scans"]
)
def get_scan_values(request, tax_rate: int, region_id: int):
    if not request.user.has_perm("moons.view_moonscan"):
        return 403, "Permission Denied!"
    profile = models.OreTaxRates.objects.filter(id=tax_rate, show_in_moon_values=True).first()
    if not profile:
        return 404, "Tax profile not offered for moon values"
    try:
        fuel = rent.fuel_for(profile)
    except rent.FuelPricesUnavailable as e:
        return 503, str(e)
    prices_updated = models.OrePrice.objects.order_by("-last_update").values_list(
        "last_update", flat=True).first()
    rentals = {
        moon_id: (contact, price) for moon_id, contact, price in models.MoonRental.objects.filter(
            end_date__isnull=True, moon__solar_system__constellation__region_id=region_id,
        ).values_list("moon_id", "contact__character_name", "price")
    }
    # whether a moon is taken is fine to show; who rents it and for how much is not
    see_rentals = request.user.has_perm("moons.view_moonrental")
    return 200, {"prices_updated": prices_updated, "fuel_30d": fuel.total_30d if fuel else None, "moons": [
        {
            "moon": {"id": v.moon_id, "name": v.name},
            "system": v.system,
            "region": v.region,
            "value": v.value_30d,
            "tax": v.tax_30d,
            "rent": rent.rent_breakdown(v.tax_30d, profile, fuel).final,
            "total_fraction": v.total_fraction,
            "ores": [{"type_id": t, "name": n, "fraction": f} for t, n, f in v.ores],
            "unpriced": v.unpriced,
            "added_at": v.added_at,
            "added_by": v.added_by,
            "rarity": v.rarity,
            "rented": v.moon_id in rentals,
            "rented_by": rentals[v.moon_id][0] if see_rentals and v.moon_id in rentals else None,
            "rental_price": rentals[v.moon_id][1] if see_rentals and v.moon_id in rentals else None,
        }
        # one region at a time: tens of thousands of scanned moons won't fit in one response
        for v in scans.moon_values(profile, region_id=region_id)
    ]}


@api.get(
    "/scans/suggestion",
    response={200: schema.RentalSuggestion, 403: str, 404: str, 503: str},
    tags=["Scans", "Rentals"]
)
def get_rental_suggestion(request, moon_id: int, tax_rate: int):
    if not _can_see_rental_suggestions(request.user):
        return 403, "Permission Denied!"
    profile = models.OreTaxRates.objects.filter(id=tax_rate, show_in_moon_values=True).first()
    if not profile:
        return 404, "Tax profile not offered for moon values"
    values = scans.moon_values(profile, moon_ids=[moon_id])
    if not values:
        return 200, {"price": None}
    try:
        fuel = rent.fuel_for(profile)
    except rent.FuelPricesUnavailable as e:
        return 503, str(e)
    # a suggestion only, never written to the rental
    return 200, {"price": rent.rent_breakdown(values[0].tax_30d, profile, fuel).final}
