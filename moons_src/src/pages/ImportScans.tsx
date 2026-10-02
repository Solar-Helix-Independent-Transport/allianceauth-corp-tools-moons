import ErrorBoundary from "../components/ErrorBoundary";
import { postScanImport, postScanPreview } from "../helpers/Api";
import { scanOre, scanResult, scanStatus } from "../types";
import { useState } from "react";
import { Accordion, Alert, Badge, Button, Col, Form, Row, Spinner, Table } from "react-bootstrap";

const STATUSES: Array<{ status: scanStatus; label: string; bg: string; open: boolean }> = [
  { status: "new", label: "New", bg: "success", open: true },
  { status: "changed", label: "Changed — will overwrite", bg: "warning", open: true },
  {
    status: "needs_change_perm",
    label: "Changed — needs change permission",
    bg: "danger",
    open: true,
  },
  { status: "unchanged", label: "Unchanged", bg: "secondary", open: false },
  { status: "rejected", label: "Rejected", bg: "danger", open: true },
];

const importable = (r: scanResult) => r.status === "new" || r.status === "changed";

const percent = (f: number | null) => (f === null ? "—" : `${(f * 100).toFixed(1)}%`);

const OreTable = ({ result }: { result: scanResult }) => {
  const showPrevious = result.status === "changed" || result.status === "needs_change_perm";
  return (
    <Table size="sm" className="small mb-0">
      <tbody>
        {result.ores.map((o: scanOre) => (
          <tr key={o.type_id}>
            <td>
              {o.name ?? `Unknown type ${o.type_id}`}
              {o.name && result.flagged.includes(o.name) && (
                <Badge bg="info" className="ms-1" title="No longer a moon ore">
                  ⚑
                </Badge>
              )}
            </td>
            {showPrevious && <td className="text-muted">{percent(o.previous)} →</td>}
            <td>{percent(o.fraction)}</td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
};

const ImportScans = () => {
  const [step, setStep] = useState<"paste" | "review" | "done">("paste");
  const [text, setText] = useState("");
  const [results, setResults] = useState<Array<scanResult>>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (call: (t: string) => Promise<Array<scanResult>>, next: "review" | "done") => {
    setBusy(true);
    setError(null);
    try {
      setResults(await call(text));
      setStep(next);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const toImport = results.filter(importable).length;

  return (
    <ErrorBoundary>
      <Row>
        <Col md={5}>
          <div className="d-flex gap-2 mb-2">
            {(["paste", "review", "done"] as const).map((s, i) => (
              <Badge key={s} bg={step === s ? "primary" : "secondary"}>
                {i + 1} · {s[0].toUpperCase() + s.slice(1)}
              </Badge>
            ))}
          </div>
          <Form.Control
            as="textarea"
            rows={14}
            value={text}
            disabled={step !== "paste"}
            onChange={(e) => setText(e.target.value)}
            className="font-monospace small"
            placeholder="Paste probe scanner moon results here — one or many moons."
          />
          <div className="d-flex gap-2 mt-2">
            {step === "paste" && (
              <Button
                disabled={!text.trim() || busy}
                onClick={() => run(postScanPreview, "review")}
              >
                Review →
              </Button>
            )}
            {step === "review" && (
              <Button variant="secondary" disabled={busy} onClick={() => setStep("paste")}>
                ← Edit paste
              </Button>
            )}
            {step === "done" && (
              <Button
                variant="secondary"
                onClick={() => {
                  setText("");
                  setResults([]);
                  setStep("paste");
                }}
              >
                Import more
              </Button>
            )}
            {busy && <Spinner size="sm" className="align-self-center" />}
          </div>
        </Col>
        <Col md={7}>
          {error && <Alert variant="danger">{error}</Alert>}
          {step === "paste" && (
            <p className="text-muted mt-4">Paste on the left, then review here.</p>
          )}
          {step !== "paste" && results.length === 0 && (
            <Alert variant="warning">No moons found in that paste.</Alert>
          )}
          {step !== "paste" && results.length > 0 && (
            <Accordion
              alwaysOpen
              defaultActiveKey={STATUSES.filter((s) => s.open).map((s) => s.status)}
            >
              {STATUSES.map(({ status, label, bg }) => {
                const group = results.filter((r) => r.status === status);
                if (!group.length) return null;
                return (
                  <Accordion.Item eventKey={status} key={status}>
                    <Accordion.Header>
                      <Badge bg={bg}>{label}</Badge>&nbsp;{group.length}
                    </Accordion.Header>
                    <Accordion.Body className="p-2">
                      {group.map((r) => (
                        <div key={r.moon_id} className="mb-2">
                          <strong>{r.name}</strong>{" "}
                          <span className="small text-muted">{r.reason}</span>
                          <OreTable result={r} />
                        </div>
                      ))}
                    </Accordion.Body>
                  </Accordion.Item>
                );
              })}
            </Accordion>
          )}
          {step === "review" && (
            <Button
              className="mt-2"
              variant="success"
              disabled={!toImport || busy}
              onClick={() => run(postScanImport, "done")}
            >
              Confirm import of {toImport} moon(s)
            </Button>
          )}
          {step === "done" && (
            <Alert variant="success" className="mt-2">
              Imported {toImport} moon(s).
            </Alert>
          )}
        </Col>
      </Row>
    </ErrorBoundary>
  );
};

export default ImportScans;
