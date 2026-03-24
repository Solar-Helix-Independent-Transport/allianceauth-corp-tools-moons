# AA Example App
try:
    from eve_sde.test_data import ModelSpec

    types_to_load = [
        45513, # Ytterbite
        46319, # Shining Ytterbite
        46318, # Bountiful Ytterbite
        46309, # Glowing Pollucite
        46301, # Shimmering Vanadinite
        46295, # Twinkling Scheelite
        46285, # Glistening Bitumens
        46290, # Copious Euxenite
    ]
    attribute_ids = 2711
    testdata_spec: list[ModelSpec] = [
        ModelSpec("ItemType", ids=types_to_load),
        ModelSpec("ItemTypeMaterials", ids=types_to_load, field="item_type_id"),
        ModelSpec("TypeDogma", ids=types_to_load, field="item_type_id"),
    ]
except ImportError:
    pass
