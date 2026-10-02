import BaseTable from "../components/BaseTable/BaseTable";
import ErrorBoundary from "../components/ErrorBoundary";
import { ErrorLoader, PanelLoader } from "../components/Loaders/Loaders";
import { getScanProfiles, getScanRegions, getScanValues } from "../helpers/Api";
import { scannedMoonValue, scannedRegion, taxProfile } from "../types";
import { createColumnHelper } from "@tanstack/react-table";
import { useState } from "react";
import { Alert, Badge, Form } from "react-bootstrap";
import { useQuery } from "react-query";

const col: any = createColumnHelper<scannedMoonValue>();

const isk = (n: number) => `${Math.round(n).toLocaleString()} ISK`;

const columns = [
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
        message={((profiles.error || regions.error || values.error) as Error).message}
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
    </ErrorBoundary>
  );
};

export default MoonValues;
