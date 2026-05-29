import { oreVol } from "../types";
import { seachOre } from "./ColumnFilter";
import { OreProgress } from "./OreProgress";
import { TimeAndSince } from "./TimeAndSince";
import { createColumnHelper } from "@tanstack/react-table";
import { Badge } from "react-bootstrap";

// typed as any to allow the custom 'width' property used by BaseTable
const col: any = createColumnHelper();

// Column widths sum to 12 at md+: time(2) + moon(3) + jackpot(1) + ore(6) = 12
export const extractionTimeColumn = col.accessor("extraction_end", {
  header: "Frack Arrival (local time)",
  width: "col-md-2",
  cell: (props: any) => <TimeAndSince stringDate={props.getValue()} />,
  enableColumnFilter: false,
});

export const jackpotColumn = col.accessor("jackpot", {
  header: "Jackpot",
  width: "col-md-1",
  cell: (props: any) =>
    props.getValue() ? (
      <div className="text-center jackpot">
        <i className="fas fa-award" style={{ fontSize: "64px" }} />
      </div>
    ) : null,
});

/** valueLabel is the full text prefix before the ISK amount, e.g. "Current Mined Value:" */
export function moonColumn(valueLabel: string, width = "col-md-3") {
  return col.accessor("moon.name", {
    header: "Moon",
    width,
    cell: (props: any) => {
      const { ObserverName, constellation, region, value } = props.cell.row.original;
      return (
        <div className="text-center">
          <h6>{props.getValue()}</h6>
          <br />
          <p className="m-0">{ObserverName}</p>
          <p>
            {constellation} - {region}
          </p>
          {value > 0 && (
            <Badge>
              {valueLabel} ${(value / 1_000_000_000).toFixed(2)}B
            </Badge>
          )}
        </div>
      );
    },
  });
}

export function oreColumn(mode: "mined" | "estimated") {
  return col.accessor("mined_ore", {
    header: "Ore Composition",
    width: "col-md-6",
    cell: (props: any) => {
      const ores: oreVol[] | undefined = props.getValue();
      const totalM3: number = props.cell.row.original.total_m3;
      if (!ores?.length) return null;
      return (
        <div>
          {ores.map((ore) => {
            const percent =
              mode === "estimated"
                ? (ore.total_volume / totalM3) * 100
                : (ore.volume / ore.total_volume) * 100;
            return (
              <OreProgress
                key={ore.type.id}
                ore={ore}
                percent={percent}
                badgePercent={(ore.total_volume / totalM3) * 100}
                value={ore.value}
                valueMessage={mode === "estimated" ? "Estimated" : "Mined"}
              />
            );
          })}
        </div>
      );
    },
    filterFn: seachOre,
  });
}
