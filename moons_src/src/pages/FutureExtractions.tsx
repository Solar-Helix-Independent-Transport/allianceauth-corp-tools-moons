import BaseTable from "../components/BaseTable/BaseTable";
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
  const columnHelper = createColumnHelper<mining>();

  const columns = [
    columnHelper.accessor("extraction_end", {
      header: "Frack Arrival",
      cell: (props: any) => <TimeAndSince stringDate={props.getValue()} />,
      enableColumnFilter: false,
    }),
    columnHelper.accessor("moon.name", {
      header: "Moon",
      cell: (props) => (
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
      cell: (props) =>
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
      cell: (props) =>
        props.getValue() ? (
          <>
            <div className="align-items-center">
              {props.getValue()?.map((ore) => {
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
