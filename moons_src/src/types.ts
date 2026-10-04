export interface KeyVal {
  name: string;
  id: string | number;
  cat?: string;
  cat_id?: string | number;
}
export interface oreVol {
  type: KeyVal;
  volume: number;
  total_volume: number;
  value: number;
}
export interface mining {
  extraction_end: string;
  moon: KeyVal;
  jackpot: boolean;
  ObserverName: string;
  system: string;
  constellation: string;
  region: string;
  mined_ore?: Array<oreVol>;
  total_m3: number;
  value: number;
}
export interface corps {
  name: string;
  char_tokens: string | number;
  corp_tokens: string | number;
  obs: string;
  frack: string;
}
export interface rentalCharacter {
  character_name: string;
  character_id: number;
  corporation_name: string;
  corporation_id: number;
  alliance_name?: string;
  alliance_id?: number;
}
export interface rentalCorporation {
  corporation_name: string;
  corporation_id: number;
  alliance_name?: string;
  alliance_id?: number;
}
export interface moonRental {
  id: number;
  moon: KeyVal;
  system: KeyVal;
  constellation: string;
  region: string;
  contact: rentalCharacter;
  corporation: rentalCorporation;
  main_character?: rentalCharacter;
  price: number;
  start_date: string;
  note: string;
  reprice_method: { id: number; tag: string } | null;
}
export type scanStatus = "new" | "unchanged" | "changed" | "needs_change_perm" | "rejected";
export interface scanOre {
  type_id: number;
  name: string | null;
  fraction: number | null;
  previous: number | null;
}
export interface scanResult {
  moon_id: number;
  name: string;
  status: scanStatus;
  reason: string;
  flagged: Array<string>;
  ores: Array<scanOre>;
}
export interface taxProfile {
  id: number;
  tag: string;
  rent_subtract_metenox_fuel: boolean;
  rent_profit_share: number;
  rent_minimum: number;
}
export interface scannedMoonValue {
  moon: KeyVal;
  system: string;
  region: string;
  value: number;
  tax: number;
  rent: number;
  total_fraction: number;
  ores: Array<{ type_id: number; name: string; fraction: number }>;
  unpriced: Array<string>;
  added_at: string;
  added_by: string | null;
  rarity: number | null;
  rented: boolean;
  rented_by: string | null;
  rental_price: number | null;
}
export interface scannedRegion {
  id: number;
  name: string;
  moons: number;
}
export interface regionCoverage {
  id: number;
  name: string;
  moons: number;
  scanned: number;
}
export interface missingMoon {
  id: number;
  name: string;
  system: string;
  constellation: string;
}
