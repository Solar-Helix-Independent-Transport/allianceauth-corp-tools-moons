import BaseTable from "../components/BaseTable/BaseTable";
import ErrorBoundary from "../components/ErrorBoundary";
import { ErrorLoader, PanelLoader } from "../components/Loaders/Loaders";
import { RarityBadge, rarityLabel } from "../components/RarityBadge";
import { TimeAndSince } from "../components/TimeAndSince";
import { getAvailableMoons, getMyRentals, getScanProfiles } from "../helpers/Api";
import { renterMoon, renterRental, taxProfile } from "../types";
import { createColumnHelper } from "@tanstack/react-table";
import { useState } from "react";
import { Alert, Card, Form } from "react-bootstrap";
import { useQuery } from "react-query";

// what renters (moons.view_moonrental) see: their own rentals and the moons on offer.
// The API returns no notes and nothing about other renters.

const isk = (n: number | null) =>
  n === null ? (
    <span className="text-muted">no scan</span>
  ) : (
    `${Math.round(n).toLocaleString()} ISK`
  );

const moonCol = (col: any) =>
  col.accessor("moon.name", {
    header: "Moon",
    cell: (props: any) => {
      const { system, region } = props.cell.row.original;
      return (
        <div>
          <strong>{props.getValue()}</strong>
          <br />
          <span className="text-muted small">
            {system} - {region}
          </span>
        </div>
      );
    },
  });

const money = (col: any, key: string, header: string) =>
  col.accessor(key, {
    header,
    cell: (props: any) => isk(props.getValue()),
    enableColumnFilter: false,
  });

const mineCol: any = createColumnHelper<renterRental>();
const mineColumns = [
  moonCol(mineCol),
  money(mineCol, "value", "Value / 30d"),
  money(mineCol, "tax", "Tax / 30d"),
  money(mineCol, "price", "Monthly Price"),
  mineCol.accessor("start_date", {
    header: "Renting Since",
    cell: (props: any) => <TimeAndSince stringDate={props.getValue()} />,
    enableColumnFilter: false,
  }),
];

const offerCol: any = createColumnHelper<renterMoon>();
const offerColumns = [
  moonCol(offerCol),
  // filter on the label ("R32 Rare"), sort on the number
  offerCol.accessor((row: renterMoon) => rarityLabel(row.rarity), {
    id: "rarity",
    header: "Rarity",
    cell: (props: any) => <RarityBadge rarity={props.cell.row.original.rarity} />,
    sortingFn: (a: any, b: any) => (a.original.rarity ?? 0) - (b.original.rarity ?? 0),
  }),
  offerCol.accessor((row: renterMoon) => row.ores.map((o) => o.name).join(", "), {
    id: "composition",
    header: "Composition",
    cell: (props: any) => {
      const { ores } = props.cell.row.original as renterMoon;
      return ores.length ? (
        <span className="small">
          {ores.map((o) => `${o.name} ${(o.fraction * 100).toFixed(0)}%`).join(", ")}
        </span>
      ) : (
        <span className="text-muted small">no scan</span>
      );
    },
  }),
  money(offerCol, "value", "Value / 30d"),
  money(offerCol, "tax", "Tax / 30d"),
  money(offerCol, "rent", "Rent / 30d"),
];

const RenterRentals = () => {
  const [profileId, setProfileId] = useState<number | null>(null);
  const profiles = useQuery(["scan-profiles"], () => getScanProfiles(), {
    refetchOnWindowFocus: false,
  });
  const selected: number | undefined = profileId ?? profiles.data?.[0]?.id;

  const mine = useQuery(["rentals-mine", selected], () => getMyRentals(selected!), {
    enabled: selected !== undefined,
    refetchOnWindowFocus: false,
  });
  const offered = useQuery(["rentals-available", selected], () => getAvailableMoons(selected!), {
    enabled: selected !== undefined,
    refetchOnWindowFocus: false,
  });

  if (profiles.isLoading) {
    return <PanelLoader />;
  }
  const error = (profiles.error || mine.error || offered.error) as any;
  if (error) {
    return (
      <ErrorLoader
        title="Failed to load rentals"
        message={error?.response?.data ?? error.message}
      />
    );
  }
  if (!profiles.data?.length) {
    return <Alert variant="info">Moon prices aren&apos;t set up yet.</Alert>;
  }

  return (
    <ErrorBoundary>
      <div className="d-flex gap-3 align-items-center mb-3">
        <Form.Label className="mb-0">Price profile</Form.Label>
        <Form.Select
          style={{ width: 260 }}
          value={selected}
          onChange={(e) => setProfileId(Number(e.target.value))}
        >
          {profiles.data.map((p: taxProfile) => (
            <option key={p.id} value={p.id}>
              {p.tag}
            </option>
          ))}
        </Form.Select>
        <span className="text-muted small ms-auto">Values per 30 days</span>
      </div>
      <Card className="mb-3">
        <Card.Header>
          <strong>My rentals</strong>
        </Card.Header>
        <Card.Body>
          <BaseTable
            isFetching={mine.isFetching}
            columns={mineColumns}
            data={mine.data ?? []}
            exportFileName="MyMoonRentals"
          />
        </Card.Body>
      </Card>
      <Card>
        <Card.Header>
          <strong>Available moons</strong>
        </Card.Header>
        <Card.Body>
          <BaseTable
            isFetching={offered.isFetching}
            columns={offerColumns}
            data={offered.data ?? []}
            initialState={{ sorting: [{ id: "value", desc: true }], pagination: { pageSize: 25 } }}
            exportFileName="AvailableMoons"
          />
        </Card.Body>
      </Card>
    </ErrorBoundary>
  );
};

export default RenterRentals;
