import BaseTable from "../components/BaseTable/BaseTable";
import { seachOre } from "../components/ColumnFilter";
import ErrorBoundary from "../components/ErrorBoundary";
import { OreColourKey } from "../components/OreColourKey";
import { OreProgress } from "../components/OreProgress";
import { TimeAndSince } from "../components/TimeAndSince";
import { getPastExtractions } from "../helpers/Api";
import { mining } from "../types";
import { createColumnHelper } from "@tanstack/react-table";
import { Badge } from "react-bootstrap";
import { useQuery } from "react-query";

const PastLedger = () => {
  const { isLoading, data } = useQuery(["extractions", "Past"], () => getPastExtractions(), {
    initialData: [],
    refetchOnWindowFocus: false,
  });
  const columnHelper: any = createColumnHelper<mining>();

  const columns = [
    columnHelper.accessor("extraction_end", {
      header: "Frack Arrival",
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
              Total Mined Value ${Number(props.cell.row.original.value / 1000000000).toFixed(2)}B
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
            <div>
              {props.getValue()?.map((ore: any) => {
                let mined = Number((ore.volume / ore.total_volume) * 100);
                return (
                  <OreProgress
                    ore={ore}
                    percent={mined}
                    badgePercent={(ore.total_volume / props.cell.row.original.total_m3) * 100}
                    value={ore.value}
                    valueMessage="Mined"
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
    //{
    //  Header: "Mined Value",
    //  Cell: (props) =>
    //    props.cell.row.original.mined_ore ? (
    //      <>
    //        $
    //        {Number(
    //          props.cell.row.original.mined_ore.reduce((p, c) => {
    //            return (p += c.value);
    //          }, 0) / 1000000000
    //        ).toFixed(2)}{" "}
    //        Bill
    //      </>
    //    ) : (
    //      <></>
    //    ),
    //},
  ];

  // const defaultSort = [
  //   {
  //     id: "extraction_end",
  //     desc: true,
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

export default PastLedger;
