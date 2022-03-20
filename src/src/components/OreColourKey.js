import React from "react";
import { Label } from "react-bootstrap";

export const OreColourMap = {
  1884: "#0D98BA",
  1921: "#FFAA1D",
  1920: "#4B8B3B",
  1922: "#E86100",
  1923: "#9B1C31",
};

export const OreColourKey = () => {
  return (
    <div className="flex-container">
      <div className="text-center">
        <Label
          bsSize="small"
          style={{
            backgroundColor: OreColourMap[1884],
            margin: "5px",
          }}
        >
          Ubiquitous Moon Asteroids
        </Label>
        <Label
          bsSize="small"
          style={{
            backgroundColor: OreColourMap[1920],
            margin: "5px",
          }}
        >
          Common Moon Asteroids
        </Label>
        <Label
          bsSize="small"
          style={{
            backgroundColor: OreColourMap[1921],
            margin: "5px",
          }}
        >
          Uncommon Moon Asteroids
        </Label>
        <Label
          bsSize="small"
          style={{
            backgroundColor: OreColourMap[1922],
            margin: "5px",
          }}
        >
          Rare Moon Asteroids
        </Label>
        <Label
          bsSize="small"
          style={{
            backgroundColor: OreColourMap[1923],
            margin: "5px",
          }}
        >
          Exceptional Moon Asteroids
        </Label>
      </div>
    </div>
  );
};
