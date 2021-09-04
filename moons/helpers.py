from .models import OrePrice, OreTax, MiningTax
from corptools.models import EveItemType, InvTypeMaterials
from django.db.models import Subquery, OuterRef


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
        return list(set(InvTypeMaterials.objects.filter(eve_type__group__category_id=OreHelper.asteroids) \
            .values_list('met_type_id', flat=True)))

    def get_ore_array():     
        inv_types = InvTypeMaterials.objects.filter(eve_type__group__category_id=OreHelper.asteroids) \
            .select_related('eve_type', 'eve_type__group', 'met_type')
        
        ore_infos = {}
        for comp in inv_types:
            if comp.eve_type.name not in ore_infos:
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


    def get_ore_array_with_value_and_taxs():
        input = OreHelper.get_ore_array_with_value()
        for t in MiningTax.objects.all():
            input[o.item_id]['value'] = o.price

        return input
