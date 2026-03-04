# AA Example App
try:
    from eve_sde.test_data import ModelSpec

    types_to_load = [46319, 46309, 46301, 46295, 46285]
    testdata_spec: list[ModelSpec] = [
        ModelSpec("ItemType", ids=types_to_load),
        ModelSpec("ItemTypeMaterials", ids=types_to_load, key = "item_type_id"),
    ]
except ImportError:
    pass
