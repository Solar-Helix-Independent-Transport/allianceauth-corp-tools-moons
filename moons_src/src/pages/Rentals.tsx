import BaseTable from "../components/BaseTable/BaseTable";
import ErrorBoundary from "../components/ErrorBoundary";
import { ErrorLoader } from "../components/Loaders/Loaders";
import { NewRentalModal } from "../components/NewRentalModal";
import { TimeAndSince } from "../components/TimeAndSince";
import { UnrentModal } from "../components/UnrentModal";
import { getPerms, getRentals, getScanProfiles, postRepriceMethod } from "../helpers/Api";
import { moonRental, taxProfile } from "../types";
import { createColumnHelper } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { Badge, Button, Form } from "react-bootstrap";
import { useQuery, useQueryClient } from "react-query";

const col: any = createColumnHelper<moonRental>();

// change_moonrental users pick the ore tax the repricing task uses, right in the table
const RepriceMethodSelect = ({
  rental,
  profiles,
}: {
  rental: moonRental;
  profiles: Array<taxProfile>;
}) => {
  const queryClient = useQueryClient();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const current = rental.reprice_method;
  // keep a method set in admin selectable even if it isn't offered on Moon Values
  const options =
    current && !profiles.some((p) => p.id === current.id) ? [current, ...profiles] : profiles;

  const change = async (id: number | null) => {
    setSaving(true);
    setError(null);
    try {
      await postRepriceMethod(rental.id, id);
      queryClient.invalidateQueries(["rentals"]);
    } catch (e: any) {
      setError(e?.response?.data ?? e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Form.Select
        size="sm"
        disabled={saving}
        value={current?.id ?? ""}
        onChange={(e) => change(e.target.value ? Number(e.target.value) : null)}
      >
        <option value="">Don&apos;t reprice</option>
        {options.map((p) => (
          <option key={p.id} value={p.id}>
            {p.tag}
          </option>
        ))}
      </Form.Select>
      {error && <div className="small text-danger">{error}</div>}
    </>
  );
};

const makeColumns = (onUnrent?: (rental: moonRental) => void, profiles?: Array<taxProfile>) => [
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
    width: "col-md-1",
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
    width: "col-md-1",
  }),
  col.accessor("corporation.corporation_name", {
    header: "Corporation",
    width: "col-md-2",
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
    width: "col-md-1",
    cell: (props: any) => <TimeAndSince stringDate={props.getValue()} />,
    enableColumnFilter: false,
  }),
  // filter on the ore tax tag, or "None"
  col.accessor((row: moonRental) => row.reprice_method?.tag ?? "None", {
    id: "reprice_method",
    header: "Reprice",
    width: "col-md-1",
    cell: (props: any) => {
      const rental: moonRental = props.cell.row.original;
      if (profiles) {
        return <RepriceMethodSelect rental={rental} profiles={profiles} />;
      }
      return rental.reprice_method ? (
        <span>{rental.reprice_method.tag}</span>
      ) : (
        <span className="text-muted">None</span>
      );
    },
  }),
  col.accessor("note", {
    header: "Notes",
    width: "col-md-2",
    // notes gain a line per change (e.g. unrents), so keep the line breaks
    cell: (props: any) => (
      <span className="small" style={{ whiteSpace: "pre-line" }}>
        {props.getValue()}
      </span>
    ),
  }),
  ...(onUnrent
    ? [
        col.display({
          id: "actions",
          header: "",
          width: "col-md-1",
          cell: (props: any) => (
            <Button
              size="sm"
              variant="outline-danger"
              onClick={() => onUnrent(props.cell.row.original)}
            >
              Unrent
            </Button>
          ),
        }),
      ]
    : []),
];

const Rentals = () => {
  const [showInvalidOnly, setShowInvalidOnly] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const perms = useQuery(["perms"], () => getPerms(), { refetchOnWindowFocus: false });
  const [unrenting, setUnrenting] = useState<moonRental | null>(null);
  const canEdit: boolean = !!perms.data?.edit_rentals;
  const profiles = useQuery(["scan-profiles"], () => getScanProfiles(), {
    enabled: canEdit,
    refetchOnWindowFocus: false,
  });
  const columns = useMemo(
    () =>
      makeColumns(
        canEdit ? setUnrenting : undefined,
        canEdit && profiles.data ? profiles.data : undefined
      ),
    [canEdit, profiles.data]
  );

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
      <div className="mb-3 d-flex justify-content-end gap-3 align-items-center">
        {perms.data?.add_rentals && (
          <Button size="sm" onClick={() => setShowNew(true)}>
            + New Rental
          </Button>
        )}
        <Form.Check
          type="switch"
          id="no-auth-filter"
          label="Show No Auth Only"
          checked={showInvalidOnly}
          onChange={(e) => setShowInvalidOnly(e.target.checked)}
        />
      </div>
      <BaseTable {...{ isFetching, columns }} data={filteredData} exportFileName="MoonRentals" />
      {showNew && <NewRentalModal show={showNew} onHide={() => setShowNew(false)} />}
      {unrenting && <UnrentModal rental={unrenting} onHide={() => setUnrenting(null)} />}
    </ErrorBoundary>
  );
};

export default Rentals;
