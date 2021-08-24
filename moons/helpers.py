from .models import OrePrice, OreTax
from corptools.models import EveItemType, InvTypeMaterials
from django.db.models import Subquery, OuterRef


class OreHelper:

    rank_ids = {
        1923: 64,
        1922:  32,
        1921: 16,
        1920: 8,
        1884: 4
    }

    asteroids = 25

    def get_ore_array(self):     
        mineral_name = EveItemType.objects.filter(type_id=OuterRef('material_type_id'))
        inv_types = InvTypeMaterials.objects.filter(type__category_id=self.asteroids) \
            .select_related('eve_type') \
            .annotate(mineral_name=Subquery(mineral_name.values('name')))
        
        ore_infos = {}
        for comp in inv_types:
            if comp.eve_type.name not in ore_infos:
                ore_infos[comp.eve_type.name] = {
                    "minerals": {},
                    "volume": comp.eve_type.packaged_volume
                    "name": eve_type.name
                }
            ore_infos[comp.eve_type.name]['minerals'][comp.mineral_name] = comp.qty
        
        return ore_infos


  