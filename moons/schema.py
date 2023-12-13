from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from ninja import Schema


class MoonPermisions(Schema):
    view_public_extractions: bool = False
    view_corp_extractions: bool = False
    view_alliance_extractions: bool = False
    view_limited_future: bool = False
    view_observations: bool = False
    view_rentals: bool = False
    edit_rentals: bool = False
    su: bool = False


class IdName(Schema):
    id: int
    name: str
    cat: Optional[str] = None
    cat_id: Optional[int] = None


class Character(Schema):
    character_name: str
    character_id: int
    corporation_name: str
    corporation_id: int
    alliance_name: Optional[str] = None
    alliance_id: Optional[int] = None


class Corporation(Schema):
    corporation_name: str
    corporation_id: int
    alliance_name: Optional[str] = None
    alliance_id: Optional[int] = None


class OreVolume(Schema):
    type: IdName
    volume: Decimal
    total_volume: Decimal
    value: float


class ExtractionEvent(Schema):
    ObserverName: str
    moon: IdName
    system: str
    constellation: str
    region: str
    extraction_end: datetime
    mined_ore: Optional[List[OreVolume]] = None
    jackpot: bool = False
    total_m3: Decimal
    value: Decimal


class MoonRental(Schema):
    moon: IdName
    system: IdName
    contact: Character
    corporation: Corporation
    price: Decimal
    start_date: datetime


class NewMoonRental(Schema):
    moon_id: int
    contact_id: int
    corporation_id: int
    price: Decimal
