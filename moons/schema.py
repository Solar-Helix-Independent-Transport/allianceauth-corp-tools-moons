from datetime import datetime
from typing import List, Optional
from ninja import Schema


class MoonPermisions(Schema):
    view_public_extractions: bool = False
    view_corp_extractions: bool = False
    view_alliance_extractions: bool = False
    view_observations: bool = False
    view_rentals: bool = False
    edit_rentals: bool = False
    su: bool = False


class IdName(Schema):
    id: int
    name: str
    cat: Optional[str]
    cat_id: Optional[int]


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
    total_volume: int
    value: float


class ExtractionEvent(Schema):
    ObserverName: str
    moon: IdName
    system: str
    constellation: str
    region: str
    extraction_end: datetime
    mined_ore: Optional[List[OreVolume]]
    jackpot: bool = False
    total_m3: int
    value: int


class MoonRental(Schema):
    moon: IdName
    system: IdName
    contact: Character
    corporation: Corporation
    price: int
    start_date: datetime


class NewMoonRental(Schema):
    moon_id: int
    contact_id: int
    corporation_id: int
    price: int
