import React from "react";
import { Panel, Label } from "react-bootstrap";
import { useQuery } from "react-query";
import { getExtractions } from "../helpers/Api";
import {
  BaseTable,
  textColumnFilter,
  colourStyles,
} from "../components/BaseTable";
import ErrorBoundary from "../components/ErrorBoundary";
import Select from "react-select";
import "./CorporateLedger.css";
import ReactTimeAgo from "react-time-ago";
import { OreColourMap, OreColourKey } from "../components/OreColourKey";

const dateFormat = Intl.DateTimeFormat("default", {
  year: "numeric",
  month: "long",
  day: "numeric",
});
const timeFormat = Intl.DateTimeFormat("default", {
  hour: "numeric",
  minute: "numeric",
  hour12: false,
});

const CorporateLedger = () => {
  const { isLoading, isFetching, error, data } = useQuery(
    ["extractions"],
    () => getExtractions(),
    {
      initialData: [],
    }
  );

  const columns = React.useMemo(
    () => [
      {
        Header: "Frack Arrival",
        accessor: "extraction_end",
        Cell: (props) => (
          <h5 className="text-center">
            {dateFormat.format(Date.parse(props.value))}{" "}
            {timeFormat.format(Date.parse(props.value))}
            <br />
            <Label className="">
              <ReactTimeAgo date={Date.parse(props.value)} />
            </Label>
          </h5>
        ),
      },
      {
        Header: "Moon Name",
        accessor: "moon.name",
        Filter: textColumnFilter,
        filter: "text",
        Cell: (props) => (
          <div className="text-center">
            <h4>{props.value}</h4>
            <br />
            <h5>{props.cell.row.original.ObserverName}</h5>
          </div>
        ),
      },
      {
        Header: "Jackpot",
        accessor: "jackpot",
        Cell: (props) =>
          props.value ? (
            <div className="text-center jackpot">
              <i class="fas fa-award" style={{ fontSize: "64px" }}></i>
            </div>
          ) : (
            <></>
          ),
      },
      {
        Header: "Ore Composition Remaining",
        accessor: "mined_ore",
        Filter: ({
          column: { setFilter, filterValue, preFilteredRows, id },
        }) => {
          const options = React.useMemo(() => {
            const options = new Set();
            if (!preFilteredRows) {
              return [];
            }
            preFilteredRows.forEach((row) => {
              if (row.values[id] !== null) {
                row.values[id].forEach((ores) => {
                  options.add(ores.type.cat);
                });
              }
            });
            return [...options.values()];
          }, [id, preFilteredRows]);
          return (
            <Select
              key={filterValue}
              title={filterValue}
              onChange={(e) => setFilter(e.value)}
              value={{ label: filterValue || "All" }}
              defaultValue={{ label: "All" }}
              styles={colourStyles}
              options={[{ id: -1, value: "", label: "All" }].concat(
                options.map((o, i) => {
                  return { id: i, value: o, label: o };
                })
              )}
            />
          );
        },
        filter: (rows, ids, filterValue) => {
          return rows.filter((row) => {
            return ids.some((id) => {
              if (!filterValue) {
                return true;
              } else {
                let rowValue = row.values[id].reduce((p, c) => {
                  return p + "  " + c.type.cat;
                }, "");
                return rowValue
                  ? rowValue.toLowerCase().includes(filterValue.toLowerCase())
                  : false;
              }
            });
          });
        },
        Cell: (props) =>
          props.value ? (
            <div className="">
              {props.value.map((ore) => {
                let mined = Number(
                  (ore.volume / ore.total_volume) * 100
                ).toFixed(1);
                return (
                  <div
                    style={{
                      display: "flex",
                      alignContent: "center",
                      justifyContent: "center",
                    }}
                  >
                    <img
                      alt={ore.type.name}
                      style={{
                        width: "32px",
                        height: "32px",
                        margin: "15px",
                        borderRadius: "30px",
                        backgroundColor: OreColourMap[ore.type.cat_id],
                      }}
                      src={
                        "https://images.evetech.net/types/" +
                        ore.type.id +
                        "/icon"
                      }
                    ></img>
                    <div
                      style={{
                        flexGrow: 1,
                      }}
                    >
                      <h5>
                        {ore.type.name}{" "}
                        <Label style={{ marginLeft: "5px" }} className="">
                          {(
                            (ore.total_volume /
                              props.cell.row.original.total_m3) *
                            100
                          ).toFixed(0)}
                          %
                        </Label>
                        {ore.value > 0 ? (
                          <Label className="" style={{ marginLeft: "5px" }}>
                            ${Number(ore.value / 1000000000).toFixed(2)}B Mined
                          </Label>
                        ) : (
                          <></>
                        )}
                        <Label
                          className="pull-right"
                          bsSize="small"
                          style={{
                            backgroundColor: OreColourMap[ore.type.cat_id],
                          }}
                        >
                          {ore.type.cat}
                        </Label>
                      </h5>
                      <div
                        className="progress"
                        style={{
                          minWidth: "250px",
                          maxWidth: "2000px",
                        }}
                      >
                        <div
                          className={
                            mined > 70
                              ? "progress-bar progress-bar-striped progress-bar-warning"
                              : "progress-bar progress-bar-striped progress-bar-info active"
                          }
                          style={{
                            width: mined + "%",
                            color: "black",
                          }}
                        >
                          {mined}
                          {"% Mined"}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <></>
          ),
      },
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
    ],
    []
  );

  const defaultSort = [
    {
      id: "extraction_end",
      desc: true,
    },
  ];

  return (
    <ErrorBoundary>
      <h1 className="text-center">Extractions</h1>
      <h5 className="text-center small">Key:</h5>
      <OreColourKey />
      <br />
      <Panel>
        <Panel.Heading className="text-center">Active Moons</Panel.Heading>
        <Panel.Body>
          <BaseTable
            {...{ isLoading, isFetching, data, columns, error, defaultSort }}
          />
        </Panel.Body>
      </Panel>
    </ErrorBoundary>
  );
};

export default CorporateLedger;
