import { getMissingScans, getScanCoverage } from "../helpers/Api";
import { missingMoon, regionCoverage } from "../types";
import BaseTable from "./BaseTable/BaseTable";
import { ErrorLoader } from "./Loaders/Loaders";
import { createColumnHelper } from "@tanstack/react-table";
import { useState } from "react";
import { Alert, Card, Form, ProgressBar, Spinner } from "react-bootstrap";
import { useQuery } from "react-query";

const REGION_KEY = "moons-scan-coverage-region";

const rememberedRegion = () => {
  try {
    return Number(localStorage.getItem(REGION_KEY)) || null;
  } catch {
    return null;
  }
};

const col: any = createColumnHelper<missingMoon>();

const columns = [
  col.accessor("constellation", { header: "Constellation" }),
  col.accessor("system", { header: "System" }),
  col.accessor("name", { header: "Moon" }),
];

export const ScanCoverage = () => {
  const [regionId, setRegionId] = useState<number | null>(rememberedRegion);

  const coverage = useQuery(["scan-coverage"], () => getScanCoverage(), {
    refetchOnWindowFocus: false,
  });
  const missing = useQuery(["scan-missing", regionId], () => getMissingScans(regionId!), {
    enabled: regionId !== null,
    refetchOnWindowFocus: false,
  });

  const pickRegion = (id: number | null) => {
    setRegionId(id);
    try {
      if (id) localStorage.setItem(REGION_KEY, String(id));
      else localStorage.removeItem(REGION_KEY);
    } catch {
      // remembering the choice is a convenience only
    }
  };

  const region: regionCoverage | undefined = coverage.data?.find(
    (r: regionCoverage) => r.id === regionId
  );

  return (
    <Card className="mt-3">
      <Card.Header className="d-flex justify-content-between align-items-center gap-2">
        <strong>Scan coverage</strong>
        <Form.Select
          size="sm"
          style={{ width: 320 }}
          value={regionId ?? ""}
          onChange={(e) => pickRegion(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">— pick a region —</option>
          {(coverage.data ?? []).map((r: regionCoverage) => (
            <option key={r.id} value={r.id}>
              {r.name} ({r.scanned.toLocaleString()} / {r.moons.toLocaleString()} scanned)
            </option>
          ))}
        </Form.Select>
      </Card.Header>
      <Card.Body>
        {!!(coverage.error || missing.error) && (
          <ErrorLoader
            title="Failed to load scan coverage"
            message={((coverage.error || missing.error) as Error).message}
          />
        )}
        {coverage.isLoading && <Spinner size="sm" />}
        {!coverage.isLoading && !region && (
          <span className="text-muted small">
            Pick a region to see which of its moons have no scan yet.
          </span>
        )}
        {region && (
          <>
            <div className="d-flex justify-content-between small mb-1">
              <span>
                {region.scanned.toLocaleString()} of {region.moons.toLocaleString()} moons scanned
              </span>
              <span className="text-muted">
                {(region.moons - region.scanned).toLocaleString()} missing
              </span>
            </div>
            <ProgressBar
              now={(region.scanned / region.moons) * 100}
              variant={region.scanned === region.moons ? "success" : "info"}
              className="mb-3"
            />
            {missing.isLoading && <Spinner size="sm" />}
            {missing.data && missing.data.length === 0 && (
              <Alert variant="success" className="mb-0">
                Every moon in {region.name} has a scan.
              </Alert>
            )}
            {missing.data && missing.data.length > 0 && (
              <BaseTable
                isFetching={missing.isFetching}
                columns={columns}
                data={missing.data}
                initialState={{ pagination: { pageSize: 25 } } as any}
                exportFileName={`MissingScans-${region.name}`}
              />
            )}
          </>
        )}
      </Card.Body>
    </Card>
  );
};
