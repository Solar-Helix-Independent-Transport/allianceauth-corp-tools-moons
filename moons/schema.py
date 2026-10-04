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
    add_rentals: bool = False
    import_scans: bool = False
    change_scans: bool = False
    view_scans: bool = False
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


class RepriceMethod(Schema):
    id: int
    tag: str


class MoonRental(Schema):
    id: int
    moon: IdName
    system: IdName
    constellation: str
    region: str
    contact: Character
    corporation: Corporation
    main_character: Optional[Character] = None
    price: Decimal
    start_date: datetime
    note: str = ""
    reprice_method: Optional[RepriceMethod] = None  # ore tax the reprice task uses; None: not repriced


class NewMoonRental(Schema):
    moon_id: int
    contact_id: int
    corporation_id: int
    price: Decimal
    note: str = ""
    reprice_method_id: Optional[int] = None


class EndMoonRental(Schema):
    note: str


class SetRepriceMethod(Schema):
    reprice_method_id: Optional[int] = None  # None: stop repricing


class ScanText(Schema):
    text: str


class ScanOre(Schema):
    type_id: int
    name: Optional[str]
    fraction: Optional[float]  # None when the ore is only in the stored scan
    previous: Optional[float]  # None when the moon has no stored scan with it


class ScanImportResult(Schema):
    moon_id: int
    name: str
    status: str
    reason: str
    flagged: List[str]
    ores: List[ScanOre]


class TaxProfile(Schema):
    id: int
    tag: str
    rent_subtract_metenox_fuel: bool
    rent_profit_share: float  # percent
    rent_minimum: int


class MoonScanOre(Schema):
    type_id: int
    name: str
    fraction: float


class ScannedMoonValue(Schema):
    moon: IdName
    system: str
    region: str
    value: float  # ISK per 30 days
    tax: float  # ISK per 30 days under the selected profile
    rent: int  # suggested monthly rent: tax less fuel, times share, rounded, with a minimum
    total_fraction: float
    ores: List[MoonScanOre]
    unpriced: List[str]
    added_at: datetime
    added_by: Optional[str]
    rarity: Optional[int]  # R-rating: 4, 8, 16, 32 or 64
    rented: bool  # has an active rental
    rented_by: Optional[str]  # contact; only with moons.view_moonrental
    rental_price: Optional[int]  # only with moons.view_moonrental


class ScannedMoonValues(Schema):
    prices_updated: Optional[datetime]
    fuel_30d: Optional[float]  # Metenox fuel subtracted from each tax; None when the profile doesn't
    moons: List[ScannedMoonValue]


class RentalSuggestion(Schema):
    price: Optional[int]  # None when the moon has no scan


class RegionCoverage(Schema):
    id: int
    name: str
    moons: int
    scanned: int


class MissingMoon(Schema):
    id: int
    name: str
    system: str
    constellation: str


class ScannedRegion(Schema):
    id: int
    name: str
    moons: int
