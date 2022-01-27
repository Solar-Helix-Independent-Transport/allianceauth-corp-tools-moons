from datetime import datetime
from typing import List, Optional
from ninja import Schema


class MoonPermisions(Schema):
    view_public_extractions: bool = False
    view_public_observations: bool = False
    view_rentals: bool = False
    edit_rentals: bool = False


class IdName(Schema):
    id: int
    name: str


class Character(Schema):
    character_name: str
    character_id: int
    corporation_name: str
    corporation_id: int
    alliance_name: Optional[str]
    alliance_id: Optional[int]


class Corporation(Schema):
    corporation_name: str
    corporation_id: int
    alliance_name: Optional[str]
    alliance_id: Optional[int]


class OreVolume(Schema):
    type: IdName
    volume: int


class ExtractionEvent(Schema):
    ObserverName: str
    moon: IdName
    extraction_end: datetime
    mined_ore: Optional[List[OreVolume]]


class MoonRenatal(Schema):
    moon: IdName
    system: IdName
    contact: Character
    corporation: Corporation
    price: int
    start_date: datetime


class NewMoonRenatal(Schema):
    moon_id: int
    contact_id: int
    corporation_id: int
    price: int
