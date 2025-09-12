import BaseTable from "../components/BaseTable/BaseTable";
import { seachOre } from "../components/ColumnFilter";
import ErrorBoundary from "../components/ErrorBoundary";
import { OreColourKey } from "../components/OreColourKey";
import { OreProgress } from "../components/OreProgress";
import { TimeAndSince } from "../components/TimeAndSince";
import { getFutureExtractions } from "../helpers/Api";
import { mining } from "../types";
import { createColumnHelper } from "@tanstack/react-table";
import { Badge } from "react-bootstrap";
import { useQuery } from "react-query";

const FutureExtractions = () => {
  const { isLoading, data } = useQuery(["future-extractions"], () => getFutureExtractions(), {
    initialData: [],
    refetchOnWindowFocus: false,
  });
  const columnHelper: any = createColumnHelper<mining>();

  const columns = [
    columnHelper.accessor("extraction_end", {
      header: "Frack Arrival (local time)",
      cell: (props: any) => <TimeAndSince stringDate={props.getValue()} />,
      enableColumnFilter: false,
    }),
    columnHelper.accessor("moon.name", {
      header: "Moon",
      cell: (props: any) => (
        <div className="text-center">
          <h6>{props.getValue()}</h6>
          <br />
          <p className="m-0">{props.cell.row.original.ObserverName}</p>
          <p>
            {props.cell.row.original.constellation} - {props.cell.row.original.region}
          </p>
          {props.cell.row.original.value > 0 && (
            <Badge>
              Value Estimate: ${Number(props.cell.row.original.value / 1000000000).toFixed(2)}B
            </Badge>
          )}
        </div>
      ),
    }),
    columnHelper.accessor("jackpot", {
      header: "Jackpot",
      cell: (props: any) =>
        props.getValue() ? (
          <div className="text-center jackpot">
            <i className="fas fa-award" style={{ fontSize: "64px" }}></i>
          </div>
        ) : (
          <></>
        ),
    }),
    columnHelper.accessor("mined_ore", {
      header: "Ore Composition",
      width: "col-lg-6 col-xl-6",
      cell: (props: any) =>
        props.getValue() ? (
          <>
            <div className="align-items-center">
              {props.getValue()?.map((ore: any) => {
                let percent = (ore.total_volume / props.cell.row.original.total_m3) * 100;
                return (
                  <OreProgress
                    ore={ore}
                    percent={percent}
                    badgePercent={(ore.total_volume / props.cell.row.original.total_m3) * 100}
                    value={ore.value}
                    valueMessage="Estimated"
                  />
                );
              })}
            </div>
          </>
        ) : (
          <></>
        ),
      filterFn: seachOre,
    }),
  ];

  // const defaultSort = [
  //   {
  //     id: "extraction_end",
  //     desc: false,
  //   },
  // ];

  return (
    <ErrorBoundary>
      <h5 className="text-center small">Key:</h5>
      <OreColourKey />
      <br />
      <BaseTable {...{ isLoading, data, columns }} />
    </ErrorBoundary>
  );
};

export default FutureExtractions;
