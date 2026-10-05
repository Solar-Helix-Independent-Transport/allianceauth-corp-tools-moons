import BaseTable from "../components/BaseTable/BaseTable";
import ErrorBoundary from "../components/ErrorBoundary";
import { ErrorLoader } from "../components/Loaders/Loaders";
import { NewRentalModal } from "../components/NewRentalModal";
import { PasteMoonsModal, PasteResult } from "../components/PasteMoonsModal";
import { TimeAndSince } from "../components/TimeAndSince";
import { UnrentModal } from "../components/UnrentModal";
import { getPerms, getRentals, getScanProfiles, postRepriceMethod } from "../helpers/Api";
import { moonKey } from "../helpers/moonPaste";
import { moonRental, taxProfile } from "../types";
import { RowSelectionState, createColumnHelper } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { Badge, Button, Form, OverlayTrigger, Tooltip } from "react-bootstrap";
import { useQuery, useQueryClient } from "react-query";

const col: any = createColumnHelper<moonRental>();

// notes gain a line per change (repricing, unrents), so show one line until asked
const NotesCell = ({ note }: { note: string }) => {
  const [open, setOpen] = useState(false);
  const text = (note ?? "").trim();
  if (!text) return <span className="text-muted small">—</span>;
  // more than fits on one line: several lines, or one long one
  const more = text.includes("\n") || text.length > 40;
  return (
    <div className="d-flex align-items-start gap-1 small">
      <span
        className={open ? "flex-grow-1" : "flex-grow-1 text-truncate"}
        style={{ whiteSpace: open ? "pre-line" : "nowrap", minWidth: 0 }}
      >
        {open ? text : text.split("\n")[0]}
      </span>
      {more && (
        <OverlayTrigger
          placement="top"
          overlay={<Tooltip id="notes-toggle">{open ? "Hide notes" : "Show all notes"}</Tooltip>}
        >
          <Button
            size="sm"
            variant="link"
            className="p-0 lh-1"
            aria-label={open ? "Hide notes" : "Show all notes"}
            onClick={() => setOpen(!open)}
          >
            <i className={`fas fa-fw ${open ? "fa-chevron-up" : "fa-chevron-down"}`} />
          </Button>
        </OverlayTrigger>
      )}
    </div>
  );
};

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
    cell: (props: any) => <NotesCell note={props.getValue()} />,
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

// pasted names -> their active rentals (in paste order) and lines with none
const rentalsFromPaste = (
  names: Array<string>,
  active: Array<moonRental>
): PasteResult<moonRental> => {
  const byName = new Map(active.map((r) => [moonKey(r.moon.name), r]));
  const result: PasteResult<moonRental> = { matched: [], problems: [] };
  names.forEach((name) => {
    const rental = byName.get(moonKey(name));
    if (rental) result.matched.push(rental);
    else result.problems.push({ name, why: "no active rental (or not a moon)" });
  });
  return result;
};

const Rentals = () => {
  const [showInvalidOnly, setShowInvalidOnly] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const perms = useQuery(["perms"], () => getPerms(), { refetchOnWindowFocus: false });
  const [unrenting, setUnrenting] = useState<Array<moonRental> | null>(null);
  const [selected, setSelected] = useState<RowSelectionState>({});
  const [pasting, setPasting] = useState(false);
  const canEdit: boolean = !!perms.data?.edit_rentals;
  const profiles = useQuery(["scan-profiles"], () => getScanProfiles(), {
    enabled: canEdit,
    refetchOnWindowFocus: false,
  });
  const columns = useMemo(
    () =>
      makeColumns(
        canEdit ? (rental: moonRental) => setUnrenting([rental]) : undefined,
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
        {canEdit && (
          <Button
            size="sm"
            variant="outline-danger"
            // matching needs the rentals loaded first
            disabled={isFetching}
            onClick={() => setPasting(true)}
          >
            Unrent from paste
          </Button>
        )}
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
      <BaseTable
        {...{ isFetching, columns }}
        data={filteredData}
        exportFileName="MoonRentals"
        selection={
          canEdit
            ? {
                getRowId: (r: moonRental) => String(r.id),
                selected,
                onChange: setSelected,
                actions: (rows: Array<moonRental>) => (
                  <Button size="sm" variant="danger" onClick={() => setUnrenting(rows)}>
                    Unrent {rows.length} selected
                  </Button>
                ),
              }
            : undefined
        }
      />
      {showNew && <NewRentalModal show={showNew} onHide={() => setShowNew(false)} />}
      {pasting && (
        <PasteMoonsModal<moonRental>
          title="Unrent moons from a list"
          help="Paste the moons whose rentals should end."
          continueLabel={(n) => `Unrent ${n} moon${n === 1 ? "" : "s"}…`}
          // every active rental, not just the ones the filters show
          resolve={async (names) => rentalsFromPaste(names, data ?? [])}
          onContinue={(rentals) => {
            setPasting(false);
            setUnrenting(rentals);
          }}
          onHide={() => setPasting(false)}
        />
      )}
      {unrenting && (
        <UnrentModal
          rentals={unrenting}
          onHide={() => setUnrenting(null)}
          onDone={() =>
            // keep anything else still ticked
            setSelected((current) => {
              const next = { ...current };
              unrenting.forEach((r) => delete next[String(r.id)]);
              return next;
            })
          }
        />
      )}
    </ErrorBoundary>
  );
};

export default Rentals;
