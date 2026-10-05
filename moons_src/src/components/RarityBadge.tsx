import { OreColourMap } from "./OreColourKey";
import { Badge } from "react-bootstrap";

// R-rating -> moon ore group, to reuse the ore colour key
const RARITY_GROUP: Record<number, number> = { 4: 1884, 8: 1920, 16: 1921, 32: 1922, 64: 1923 };
const RARITY_NAME: Record<number, string> = {
  4: "Ubiquitous",
  8: "Common",
  16: "Uncommon",
  32: "Rare",
  64: "Exceptional",
};

export const rarityLabel = (rarity: number | null) =>
  rarity ? `R${rarity} ${RARITY_NAME[rarity]}` : "None";

export const RarityBadge = ({ rarity }: { rarity: number | null }) => {
  if (!rarity) {
    return <span className="text-muted">-</span>;
  }
  return (
    <Badge className={`${(OreColourMap as any)[RARITY_GROUP[rarity]]} fw-normal`}>
      {rarityLabel(rarity)}
    </Badge>
  );
};
