from typing import Dict

from eve_sde.models import ItemTypeMaterials, TypeDogma

from .models import OrePrice, OreTax

FRACK_WINDOW_EARLY_DAYS = -2
FRACK_WINDOW_LATE_DAYS = 5


class OreHelper:

    rank_ids = {
        1923: "exceptional_rate",
        1922: "rare_rate",
        1921: "uncommon_rate",
        1920: "common_rate",
        1884: "ubiquitous_rate"
    }

    asteroids_category_id = 25
    minerals_group_id = 18
    base_ore_dogma_attribute_id = 2711

    def get_mineral_array():
        return list(
            set(
                ItemTypeMaterials.objects.filter(
                    item_type__group__category_id=OreHelper.asteroids_category_id
                ).values_list(
                    'material_item_type_id',
                    flat=True
                )
            )
        )

    def get_inv_types():
        return ItemTypeMaterials.objects.filter(
            item_type__group__category_id=OreHelper.asteroids_category_id
        ).select_related(
            'item_type',
            'item_type__group',
            'material_item_type'
        )

    def get_base_attributes():
        base_attributes = TypeDogma.objects.filter(
            item_type__group__category_id=OreHelper.asteroids_category_id,
            dogma_attribute__id=OreHelper.base_ore_dogma_attribute_id
        )
        base_types = {}
        for ba in base_attributes:
            base_types[ba.item_type_id] = ba.value
        return base_types

    def get_rarity(component: ItemTypeMaterials):
        return OreHelper.rank_ids[
            component.item_type.group_id
        ] if component.item_type.group_id in OreHelper.rank_ids else "ore_rate"

    def get_base_ore_values(component: ItemTypeMaterials, base_types: dict):
        rarity = OreHelper.get_rarity(component)
        return {
            "minerals": {},
            "volume": component.item_type.packaged_volume if component.item_type.packaged_volume else component.item_type.volume,
            "model": component.item_type,
            "rarity": rarity,
            "portion": component.item_type.portion_size,
            "base_ore_id": base_types.get(component.item_type.pk, False)
        }

    def get_ore_array():
        inv_types = OreHelper.get_inv_types()
        base_types = OreHelper.get_base_attributes()
        ore_infos = {}
        for comp in inv_types:
            if comp.item_type.pk not in ore_infos:
                ore_infos[comp.item_type.pk] = OreHelper.get_base_ore_values(comp, base_types)
            ore_infos[comp.item_type.pk]['minerals'][comp.material_item_type.name] = comp.quantity

        return ore_infos

    def get_detailed_ore_array():
        inv_types = OreHelper.get_inv_types()
        base_types = OreHelper.get_base_attributes()
        base_types = OreHelper.get_base_attributes()
        ore_infos = {}
        for comp in inv_types:
            if comp.item_type.pk not in ore_infos:
                ore_infos[comp.item_type.pk] = OreHelper.get_base_ore_values(comp, base_types)
            ore_infos[comp.item_type.pk]['minerals'][comp.material_item_type.name] = {
                "grp": comp.material_item_type.group_id,
                "qty": comp.quantity
            }

        return ore_infos

    def get_ore_array_with_value():
        input = OreHelper.get_ore_array()
        for o in OrePrice.objects.all():
            if o.goo_only:
                input[o.item_id]['value_goo'] = o.price
            else:
                input[o.item_id]['value'] = o.price
        return input

    def get_ore_array_with_value_and_taxes():
        input = OreHelper.get_ore_array_with_value()
        for t in OreTax.objects.all().select_related("tax"):
            if "tax" not in input[t.item_id]:
                input[t.item_id]['tax'] = {}
            input[t.item_id]['tax'][t.tax.tag] = t.price
        return input

    def set_prices(price_cache: Dict, price_source="the_forge", goo_only=False):
        ores = OreHelper.get_detailed_ore_array()
        for ore, minerals in ores.items():
            price = 0
            for mineral, detail in minerals["minerals"].items():
                if detail["grp"] == OreHelper.minerals_group_id and goo_only:
                    continue
                else:
                    price = price + (
                        detail["qty"] *
                        price_cache[mineral][price_source]
                    )
            OrePrice.objects.update_or_create(
                item=minerals['model'],
                goo_only=goo_only,
                defaults={
                    "price": price / minerals['portion']
                }
            )


def what_frack_id(fracks: dict, observation: dict):
    """
        takes dict of fracks, and a mining observation dict and returns coresponding frack
    """
    date = observation["last_updated"]
    for id, f in fracks.items():
        if f['structure_id'] == observation['structure']:
            compare_to = f["extraction_end"]
            diff = date - compare_to
            if FRACK_WINDOW_EARLY_DAYS <= diff.days <= FRACK_WINDOW_LATE_DAYS:
                return id

    return False


def calculate_split_value(prices):
    """
        Calculate Split price from Fuzz API Data
    """
    buy = float(prices["buy"]["max"])
    sell = float(prices["sell"]["min"])
    return ((buy + sell) / 2)
