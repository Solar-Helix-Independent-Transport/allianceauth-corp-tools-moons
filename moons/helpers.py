from typing import Dict
from .models import MiningObservation, OrePrice, OreTax, MiningTax
from corptools.models import EveItemType, InvTypeMaterials, OreTaxRates
from django.db.models import Subquery, OuterRef
from django.utils import timezone


class OreHelper:

    rank_ids = {
        1923: "exceptional_rate",
        1922: "rare_rate",
        1921: "uncommon_rate",
        1920: "common_rate",
        1884: "ubiquitous_rate"
    }

    asteroids = 25

    def get_mineral_array():
        return list(set(InvTypeMaterials.objects.filter(eve_type__group__category_id=OreHelper.asteroids)
                        .values_list('met_type_id', flat=True)))

    def get_ore_array():
        inv_types = InvTypeMaterials.objects.filter(eve_type__group__category_id=OreHelper.asteroids) \
            .select_related('eve_type', 'eve_type__group', 'met_type')

        ore_infos = {}
        for comp in inv_types:
            if comp.eve_type.pk not in ore_infos:
                rarity = OreHelper.rank_ids[comp.eve_type.group_id] if comp.eve_type.group_id in OreHelper.rank_ids else "ore_rate"
                ore_infos[comp.eve_type.pk] = {
                    "minerals": {},
                    "volume": comp.eve_type.packaged_volume,
                    "model": comp.eve_type,
                    "rarity": rarity,
                    "portion": comp.eve_type.portion_size
                }
            ore_infos[comp.eve_type.pk]['minerals'][comp.met_type.name] = comp.qty

        return ore_infos

    def get_ore_array_with_value():
        input = OreHelper.get_ore_array()
        for o in OrePrice.objects.all():
            input[o.item_id]['value'] = o.price

        return input

    def get_ore_array_with_value_and_taxes():
        input = OreHelper.get_ore_array_with_value()
        for t in OreTax.objects.all().select_related("tax"):
            if "tax" not in input[t.item_id]:
                input[t.item_id]['tax'] = {}
            input[t.item_id]['tax'][t.tax.tag] = t.price
        return input

    def set_prices(price_cache: Dict, price_source="the_forge"):
        ores = OreHelper.get_ore_array()

        for ore, minerals in ores.items():
            price = 0
            for mineral, qty in minerals["minerals"].items():
                price = price + (qty * price_cache[mineral][price_source])

            OrePrice.objects.update_or_create(item=minerals['model'],
                                              defaults={
                "price": price/minerals['portion']
            })


def what_frack_id(fracks: dict, observation: dict):
    """
        takes dict of fracks, and a mining observation dict and returns coresponding frack
    """
    date = observation["last_updated"]
    for id, f in fracks.items():
        if f['structure_id'] == observation['structure']:
            compare_to = f["extraction_end"]
            diff = date - compare_to
            if -2 <= diff.days <= 5:
                return id

    return False


def calculate_split_value(prices):
    """
        Calculate Split price from Fuzz API Data
    """
    buy = float(prices["buy"]["max"])
    sell = float(prices["sell"]["min"])
    return ((buy + sell) / 2)
