import BaseTable from "../components/BaseTable/BaseTable";
import ErrorBoundary from "../components/ErrorBoundary";
import { ErrorLoader, PanelLoader } from "../components/Loaders/Loaders";
import { NewRentalModal } from "../components/NewRentalModal";
import { OreColourMap } from "../components/OreColourKey";
import { getPerms, getScanProfiles, getScanRegions, getScanValues } from "../helpers/Api";
import { scannedMoonValue, scannedRegion, taxProfile } from "../types";
import { createColumnHelper } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { Alert, Badge, Button, Form } from "react-bootstrap";
import { useQuery } from "react-query";

const col: any = createColumnHelper<scannedMoonValue>();

// R-rating -> moon ore group, to reuse the ore colour key
const RARITY_GROUP: Record<number, number> = { 4: 1884, 8: 1920, 16: 1921, 32: 1922, 64: 1923 };
const RARITY_NAME: Record<number, string> = {
  4: "Ubiquitous",
  8: "Common",
  16: "Uncommon",
  32: "Rare",
  64: "Exceptional",
};

const rarityLabel = (rarity: number | null) =>
  rarity ? `R${rarity} ${RARITY_NAME[rarity]}` : "None";

const isk = (n: number) => `${Math.round(n).toLocaleString()} ISK`;

// how the profile turns tax into rent, e.g. "Rent: 65% of (tax - 795,600,000 ISK fuel), at least 100,000,000 ISK"
const rentRule = (profile: taxProfile, fuel: number | null | undefined) => {
  let taxed = "tax";
  if (profile.rent_subtract_metenox_fuel) {
    taxed = fuel != null ? `(tax - ${isk(fuel)} Metenox fuel)` : "(tax - Metenox fuel)";
  }
  const share =
    profile.rent_profit_share === 100 ? taxed : `${profile.rent_profit_share}% of ${taxed}`;
  const minimum = profile.rent_minimum > 0 ? `, at least ${isk(profile.rent_minimum)}` : "";
  return `Rent: ${share}, rounded to a million${minimum}`;
};

const rentalCell = (row: scannedMoonValue, onRent?: (row: scannedMoonValue) => void) => {
  if (row.rented) {
    return (
      <span>
        <Badge bg="secondary">Rented</Badge>
        {row.rented_by && (
          <>
            <br />
            <span className="text-muted small">
              {row.rented_by}
              {row.rental_price != null && ` · ${isk(row.rental_price)}`}
            </span>
          </>
        )}
      </span>
    );
  }
  return (
    <span className="d-flex gap-2 align-items-center">
      <Badge bg="success">Available</Badge>
      {onRent && (
        <Button size="sm" variant="outline-primary" onClick={() => onRent(row)}>
          Rent
        </Button>
      )}
    </span>
  );
};

const makeColumns = (onRent?: (row: scannedMoonValue) => void) => [
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
  }),
  // filter on the label ("R32 Rare"), sort on the number so R64 ranks above R8
  col.accessor((row: scannedMoonValue) => rarityLabel(row.rarity), {
    id: "rarity",
    header: "Rarity",
    cell: (props: any) => {
      const rarity: number | null = props.cell.row.original.rarity;
      if (!rarity) {
        return <span className="text-muted">-</span>;
      }
      return (
        <Badge className={`${(OreColourMap as any)[RARITY_GROUP[rarity]]} fw-normal`}>
          {rarityLabel(rarity)}
        </Badge>
      );
    },
    sortingFn: (a: any, b: any) => (a.original.rarity ?? 0) - (b.original.rarity ?? 0),
  }),
  col.accessor((row: scannedMoonValue) => row.ores.map((o) => o.name).join(", "), {
    id: "composition",
    header: "Composition",
    cell: (props: any) => {
      const { ores, total_fraction, unpriced } = props.cell.row.original as scannedMoonValue;
      return (
        <span className="small">
          {ores.map((o) => `${o.name} ${(o.fraction * 100).toFixed(0)}%`).join(", ")}
          {total_fraction < 0.995 && (
            <Badge bg="secondary" className="ms-1">
              {(total_fraction * 100).toFixed(0)}% total
            </Badge>
          )}
          {unpriced.length > 0 && (
            <Badge bg="warning" text="dark" className="ms-1">
              unpriced: {unpriced.join(", ")}
            </Badge>
          )}
        </span>
      );
    },
  }),
  col.accessor("value", {
    header: "Value / 30d",
    cell: (props: any) => <span>{isk(props.getValue())}</span>,
    enableColumnFilter: false,
  }),
  col.accessor("tax", {
    header: "Tax / 30d",
    cell: (props: any) => <span>{isk(props.getValue())}</span>,
    enableColumnFilter: false,
  }),
  col.accessor("rent", {
    header: "Rent / 30d",
    cell: (props: any) => <span>{isk(props.getValue())}</span>,
    enableColumnFilter: false,
  }),
  // filter on "Rented" / "Available"
  col.accessor((row: scannedMoonValue) => (row.rented ? "Rented" : "Available"), {
    id: "rental",
    header: "Rental",
    cell: (props: any) => rentalCell(props.cell.row.original, onRent),
  }),
  col.accessor("added_by", {
    header: "Scanned",
    cell: (props: any) => {
      const { added_at } = props.cell.row.original;
      return (
        <span className="small">
          {new Date(added_at).toLocaleDateString()}
          <br />
          <span className="text-muted">{props.getValue() ?? "Unknown"}</span>
        </span>
      );
    },
  }),
];

const MoonValues = () => {
  const [profileId, setProfileId] = useState<number | null>(null);
  const [regionId, setRegionId] = useState<number | null>(null);

  const profiles = useQuery(["scan-profiles"], () => getScanProfiles(), {
    refetchOnWindowFocus: false,
  });
  const regions = useQuery(["scan-regions"], () => getScanRegions(), {
    refetchOnWindowFocus: false,
  });
  const selected: number | undefined = profileId ?? profiles.data?.[0]?.id;
  const profile: taxProfile | undefined = profiles.data?.find((p: taxProfile) => p.id === selected);
  const perms = useQuery(["perms"], () => getPerms(), { refetchOnWindowFocus: false });
  const [renting, setRenting] = useState<scannedMoonValue | null>(null);
  const canRent: boolean = !!perms.data?.add_rentals;
  const columns = useMemo(() => makeColumns(canRent ? setRenting : undefined), [canRent]);

  // one region at a time: all scanned moons together is far too much for one page
  const values = useQuery(
    ["scan-values", selected, regionId],
    () => getScanValues(selected!, regionId!),
    { enabled: selected !== undefined && regionId !== null, refetchOnWindowFocus: false }
  );

  if (profiles.isLoading || regions.isLoading) {
    return <PanelLoader />;
  }
  if (profiles.error || regions.error || values.error) {
    return (
      <ErrorLoader
        title="Failed to load moon values"
        message={
          ((profiles.error || regions.error || values.error) as any)?.response?.data ??
          ((profiles.error || regions.error || values.error) as Error).message
        }
      />
    );
  }
  if (!profiles.data?.length) {
    return (
      <Alert variant="info">
        No tax profiles are offered for moon values. Tick "Show in moon values" on an Ore Tax Rates
        profile in admin.
      </Alert>
    );
  }

  return (
    <ErrorBoundary>
      <div className="d-flex gap-3 align-items-center mb-2">
        <Form.Label className="mb-0">Region</Form.Label>
        <Form.Select
          style={{ width: 260 }}
          value={regionId ?? ""}
          onChange={(e) => setRegionId(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">— pick a region —</option>
          {(regions.data ?? []).map((r: scannedRegion) => (
            <option key={r.id} value={r.id}>
              {r.name} ({r.moons.toLocaleString()})
            </option>
          ))}
        </Form.Select>
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
        <span className="text-muted small ms-auto">
          Per 30 days
          {values.data?.prices_updated &&
            ` · prices updated ${new Date(values.data.prices_updated).toLocaleString()}`}
        </span>
      </div>
      {profile && (
        <div className="text-muted small mb-2">{rentRule(profile, values.data?.fuel_30d)}</div>
      )}
      {regionId === null ? (
        <Alert variant="secondary">Pick a region to rank its scanned moons.</Alert>
      ) : (
        <BaseTable
          isLoading={values.isLoading}
          isFetching={values.isFetching}
          columns={columns}
          data={values.data?.moons ?? []}
          initialState={
            { sorting: [{ id: "value", desc: true }], pagination: { pageSize: 25 } } as any
          }
          exportFileName="MoonValues"
        />
      )}
      {renting && (
        <NewRentalModal
          show
          onHide={() => setRenting(null)}
          initialMoon={{ label: renting.moon.name, value: Number(renting.moon.id) }}
          initialPrice={renting.rent}
          initialProfileId={selected}
        />
      )}
    </ErrorBoundary>
  );
};

export default MoonValues;
