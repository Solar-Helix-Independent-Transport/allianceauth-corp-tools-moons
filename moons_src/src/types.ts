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
  moon: KeyVal;
  system: KeyVal;
  constellation: string;
  region: string;
  contact: rentalCharacter;
  corporation: rentalCorporation;
  main_character?: rentalCharacter;
  price: number;
  start_date: string;
}
