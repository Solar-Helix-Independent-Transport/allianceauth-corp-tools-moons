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
