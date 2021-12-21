from decimal import InvalidOperation
from ninja import Schema


class MoonName(Schema):
    moon_id: int
    name: str


class CharacterName(Schema):
    character_id: int
    character_name: str


class MinedOres(Schema):
    type_id: int
    mined: int
    name: str