import ErrorBoundary from "../components/ErrorBoundary";
import { postScanImport, postScanPreview } from "../helpers/Api";
import { scanOre, scanResult, scanStatus } from "../types";
import { useState } from "react";
import {
  Accordion,
  Alert,
  Badge,
  Button,
  Card,
  Col,
  Form,
  Row,
  Spinner,
  Table,
} from "react-bootstrap";

const STATUSES: Array<{ status: scanStatus; label: string; bg: string; open: boolean }> = [
  { status: "new", label: "New", bg: "success", open: true },
  { status: "changed", label: "Changed", bg: "warning", open: true },
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

const statusLabel = (status: scanStatus, label: string, done: boolean) =>
  status === "changed" ? `${label} — ${done ? "overwritten" : "will overwrite"}` : label;

const moons = (n: number) => `${n} moon${n === 1 ? "" : "s"}`;

const STEPS = {
  paste: "Step 1 of 3 · Paste your scan",
  review: "Step 2 of 3 · Check what will change",
  done: "Step 3 of 3 · Done",
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

  const startOver = () => {
    setText("");
    setResults([]);
    setError(null);
    setStep("paste");
  };

  const toImport = results.filter(importable).length;
  const lines = text.split(/\r?\n/).filter((l) => l.trim()).length;

  return (
    <ErrorBoundary>
      <Card>
        <Card.Header className="d-flex justify-content-between align-items-center">
          <strong>Import moon scans</strong>
          <span className="small text-muted">{STEPS[step]}</span>
        </Card.Header>
        <Card.Body>
          {error && <Alert variant="danger">{error}</Alert>}

          {step === "paste" && (
            <>
              <Form.Text as="p" className="mt-0">
                In game, open the probe scanner&apos;s moon results, select the rows and copy them
                (Ctrl+C). One or many moons at once, any client language.
              </Form.Text>
              <Form.Control
                as="textarea"
                rows={10}
                value={text}
                onChange={(e) => setText(e.target.value)}
                className="font-monospace small"
                placeholder="Paste moon scan results here"
                autoFocus
              />
            </>
          )}

          {step !== "paste" && (
            <>
              {step === "done" && (
                <Alert variant="success">
                  Imported {moons(toImport)}. Values update straight away on Moon Values.
                </Alert>
              )}
              <div className="d-flex flex-wrap gap-2 align-items-center mb-3">
                <span className="small text-muted me-1">
                  {lines} line{lines === 1 ? "" : "s"} pasted, {moons(results.length)} found:
                </span>
                {STATUSES.map(({ status, label, bg }) => {
                  const count = results.filter((r) => r.status === status).length;
                  return count ? (
                    <Badge key={status} bg={bg}>
                      {count} {statusLabel(status, label, step === "done")}
                    </Badge>
                  ) : null;
                })}
                {results.some((r) => r.flagged.length) && (
                  <span className="small text-muted ms-auto">
                    <Badge bg="info">⚑</Badge> old scan: no longer a moon ore, kept anyway
                  </span>
                )}
              </div>
              {results.length === 0 ? (
                <Alert variant="warning" className="mb-0">
                  No moons found in that paste. Check it was copied from the probe scanner&apos;s
                  moon results.
                </Alert>
              ) : (
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
                          <Badge bg={bg}>{statusLabel(status, label, step === "done")}</Badge>
                          &nbsp;{moons(group.length)}
                        </Accordion.Header>
                        <Accordion.Body className="p-2">
                          <Row xs={1} md={2} xl={3} className="g-3">
                            {group.map((r) => (
                              <Col key={r.moon_id}>
                                <strong>{r.name}</strong>{" "}
                                <span className="small text-muted">{r.reason}</span>
                                <OreTable result={r} />
                              </Col>
                            ))}
                          </Row>
                        </Accordion.Body>
                      </Accordion.Item>
                    );
                  })}
                </Accordion>
              )}
            </>
          )}
        </Card.Body>
        <Card.Footer className="d-flex justify-content-between align-items-center gap-2">
          <span className="small text-muted">
            {step === "review" &&
              (toImport
                ? "Only new and changed moons are saved. Nothing is saved until you import."
                : "Nothing new to import from this paste.")}
          </span>
          <div className="d-flex gap-2 align-items-center">
            {busy && <Spinner size="sm" />}
            {step === "paste" && (
              <Button
                disabled={!text.trim() || busy}
                onClick={() => run(postScanPreview, "review")}
              >
                Preview import
              </Button>
            )}
            {step === "review" && (
              <>
                <Button variant="secondary" disabled={busy} onClick={() => setStep("paste")}>
                  Edit paste
                </Button>
                <Button
                  variant="success"
                  disabled={!toImport || busy}
                  onClick={() => run(postScanImport, "done")}
                >
                  Import {moons(toImport)}
                </Button>
              </>
            )}
            {step === "done" && <Button onClick={startOver}>Import more scans</Button>}
          </div>
        </Card.Footer>
      </Card>
    </ErrorBoundary>
  );
};

export default ImportScans;
