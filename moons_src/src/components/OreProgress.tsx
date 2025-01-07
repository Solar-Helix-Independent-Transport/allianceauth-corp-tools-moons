import { OreColourMap } from "./OreColourKey";
import { Badge } from "react-bootstrap";

export const OreProgress = ({
  ore,
  percent,
  badgePercent,
  value = 0,
  valueMessage = "",
}: {
  ore: any;
  percent: number;
  badgePercent: number;
  value?: number;
  valueMessage?: string;
}) => {
  return (
    <div className="d-flex align-items-center">
      <img
        alt={ore.type.name}
        style={{
          width: "30px",
          height: "30px",
          margin: "15px",
          borderRadius: "30px",
        }}
        className={`${OreColourMap[ore.type.cat_id as keyof typeof OreColourMap]}`}
        src={"https://images.evetech.net/types/" + ore.type.id + "/icon"}
      ></img>
      <div
        style={{
          flexGrow: 1,
        }}
      >
        {ore.type.name}{" "}
        <div className="float-end">
          <Badge pill className="fw-normal">
            {badgePercent.toFixed(0)}% of Ore Composition
          </Badge>
          {value > 0 ? (
            <Badge pill className="fw-normal">
              ${Number(value / 1000000000).toFixed(1)}B {valueMessage}
            </Badge>
          ) : (
            <></>
          )}
          <Badge
            pill
            className={`pull-right fw-normal ${
              OreColourMap[ore.type.cat_id as keyof typeof OreColourMap]
            }`}
          >
            {ore.type.cat}
          </Badge>
        </div>
        <div className="progress my-1">
          <div
            className={`progress-bar progress-bar-striped bg-info fw-bold ${
              OreColourMap[ore.type.cat_id as keyof typeof OreColourMap]
            }`}
            style={{
              width: percent + "%",
            }}
          >
            {percent.toFixed(0)}
            {"%"}
          </div>
        </div>
      </div>
    </div>
  );
};
