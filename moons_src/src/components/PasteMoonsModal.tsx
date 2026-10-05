import { parseMoonNames } from "../helpers/moonPaste";
import { useState } from "react";
import { Alert, Badge, Button, Form, Modal, Spinner } from "react-bootstrap";

export interface PasteProblem {
  name: string;
  why: string;
}

export interface PasteResult<T> {
  matched: Array<T>;
  problems: Array<PasteProblem>;
}

// paste moon names, see what matched and what didn't, then hand the matches to a bulk action
export function PasteMoonsModal<T>({
  title,
  help,
  continueLabel,
  resolve,
  onContinue,
  onHide,
}: {
  title: string;
  help: string;
  continueLabel: (count: number) => string;
  resolve: (names: Array<string>) => Promise<PasteResult<T>>;
  onContinue: (matched: Array<T>) => void;
  onHide: () => void;
}) {
  const [text, setText] = useState("");
  const [result, setResult] = useState<PasteResult<T> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const names = parseMoonNames(text);

  const check = async () => {
    setBusy(true);
    setError(null);
    try {
      setResult(await resolve(names));
    } catch (e: any) {
      setError(e?.response?.data ?? e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal show onHide={onHide} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>{title}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        {!result ? (
          <>
            <Form.Text as="p" className="mt-0">
              {help} One moon per line, e.g. <code>FM-JK5 IX - Moon 12</code>.
            </Form.Text>
            <Form.Control
              as="textarea"
              rows={12}
              autoFocus
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="font-monospace small"
              placeholder="Paste moon names here"
            />
            <div className="small text-muted mt-1">
              {names.length} moon{names.length === 1 ? "" : "s"}
            </div>
          </>
        ) : (
          <>
            <div className="d-flex gap-2 mb-2">
              <Badge bg="success">{result.matched.length} ready</Badge>
              {result.problems.length > 0 && (
                <Badge bg="warning" text="dark">
                  {result.problems.length} skipped
                </Badge>
              )}
            </div>
            {result.problems.length > 0 && (
              <Alert variant="warning" className="small">
                These lines won&apos;t be included:
                <ul className="mb-0 mt-1" style={{ maxHeight: "30vh", overflowY: "auto" }}>
                  {result.problems.map((p) => (
                    <li key={p.name}>
                      <strong>{p.name}</strong>: {p.why}
                    </li>
                  ))}
                </ul>
              </Alert>
            )}
            {result.matched.length === 0 && (
              <Alert variant="secondary" className="mb-0">
                Nothing to continue with.
              </Alert>
            )}
          </>
        )}
      </Modal.Body>
      <Modal.Footer>
        {busy && <Spinner size="sm" />}
        {!result ? (
          <Button disabled={!names.length || busy} onClick={check}>
            Check {names.length} moon{names.length === 1 ? "" : "s"}
          </Button>
        ) : (
          <>
            <Button variant="secondary" onClick={() => setResult(null)}>
              Edit paste
            </Button>
            <Button disabled={!result.matched.length} onClick={() => onContinue(result.matched)}>
              {continueLabel(result.matched.length)}
            </Button>
          </>
        )}
      </Modal.Footer>
    </Modal>
  );
}
