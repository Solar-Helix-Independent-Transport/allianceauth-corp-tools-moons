import BaseTable from "../components/BaseTable/BaseTable";
import ErrorBoundary from "../components/ErrorBoundary";
import { ErrorLoader } from "../components/Loaders/Loaders";
import { TimeAndSince } from "../components/TimeAndSince";
import { getRentals } from "../helpers/Api";
import { moonRental } from "../types";
import { createColumnHelper } from "@tanstack/react-table";
import { useState } from "react";
import { Badge, Form } from "react-bootstrap";
import { useQuery } from "react-query";

const col: any = createColumnHelper<moonRental>();

const columns = [
  col.accessor("moon.name", {
    header: "Moon",
    width: "col-md-2",
    cell: (props: any) => {
      const { system, constellation, region } = props.cell.row.original;
      return (
        <div>
          <strong>{props.getValue()}</strong>
          <br />
          <span className="text-muted small">{system.name}</span>
          <br />
          <span className="text-muted small">
            {constellation} - {region}
          </span>
        </div>
      );
    },
  }),
  col.accessor("main_character.character_name", {
    header: "Main Character",
    width: "col-md-2",
    cell: (props: any) => {
      const { main_character } = props.cell.row.original;
      if (!main_character) {
        return <Badge bg="danger">No Auth</Badge>;
      }
      return <span>{main_character.character_name}</span>;
    },
  }),
  col.accessor("contact.character_name", {
    header: "Contact",
    width: "col-md-2",
  }),
  col.accessor("corporation.corporation_name", {
    header: "Corporation",
    width: "col-md-3",
  }),
  col.accessor("price", {
    header: "Monthly Price",
    width: "col-md-1",
    cell: (props: any) => {
      const price: number = props.getValue();
      return <span>{price.toLocaleString()} ISK</span>;
    },
    enableColumnFilter: false,
  }),
  col.accessor("start_date", {
    header: "Renting Since",
    width: "col-md-2",
    cell: (props: any) => <TimeAndSince stringDate={props.getValue()} />,
    enableColumnFilter: false,
  }),
];

const Rentals = () => {
  const [showInvalidOnly, setShowInvalidOnly] = useState(false);

  const { isFetching, error, data } = useQuery(["rentals"], () => getRentals(), {
    initialData: [],
    refetchOnWindowFocus: false,
  });

  if (error) {
    return <ErrorLoader title="Failed to load rentals" message={(error as Error).message} />;
  }

  const filteredData = showInvalidOnly
    ? (data ?? []).filter((r: moonRental) => !r.main_character)
    : data;

  return (
    <ErrorBoundary>
      <div className="mb-3 d-flex justify-content-end">
        <Form.Check
          type="switch"
          id="no-auth-filter"
          label="Show No Auth Only"
          checked={showInvalidOnly}
          onChange={(e) => setShowInvalidOnly(e.target.checked)}
        />
      </div>
      <BaseTable {...{ isFetching, columns }} data={filteredData} exportFileName="MoonRentals" />
    </ErrorBoundary>
  );
};

export default Rentals;
