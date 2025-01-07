import Styles from "./OreColourKey.module.css";
import Badge from "react-bootstrap/Badge";

export const OreColourMap = {
  1884: Styles.ore1884,
  1921: Styles.ore1920,
  1920: Styles.ore1921,
  1922: Styles.ore1922,
  1923: Styles.ore1923,
};

export const OreColourKey = () => {
  return (
    <div className="flex-container">
      <div className="text-center">
        <Badge className={`${Styles.ore1884} fw-normal mx-1`}>Ubiquitous Moon Asteroids</Badge>
        <Badge className={`${Styles.ore1920} fw-normal mx-1`}>Common Moon Asteroids</Badge>
        <Badge className={`${Styles.ore1921} fw-normal mx-1`}>Uncommon Moon Asteroids</Badge>
        <Badge className={`${Styles.ore1922} fw-normal mx-1`}>Rare Moon Asteroids</Badge>
        <Badge className={`${Styles.ore1923} fw-normal mx-1`}>Exceptional Moon Asteroids</Badge>
      </div>
    </div>
  );
};
