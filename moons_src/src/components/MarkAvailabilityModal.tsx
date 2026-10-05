import { postMoonAvailability } from "../helpers/Api";
import { useState } from "react";
import { Alert, Button, ButtonGroup, Form, Modal, ToggleButton } from "react-bootstrap";
import { useQueryClient } from "react-query";

export interface MarkItem {
  id: number;
  name: string;
  place: string;
}

// mark moons available or unavailable for rent; all or nothing
export const MarkAvailabilityModal = ({
  moons,
  initialAvailable = null,
  onHide,
  onDone,
}: {
  moons: Array<MarkItem>;
  // preset from the button that opened it; null lets the user choose (e.g. from a paste)
  initialAvailable?: boolean | null;
  onHide: () => void;
  onDone?: () => void;
}) => {
  const queryClient = useQueryClient();
  const [available, setAvailable] = useState<boolean | null>(initialAvailable);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const count = `${moons.length} moon${moons.length === 1 ? "" : "s"}`;

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await postMoonAvailability(
        moons.map((m) => m.id),
        available!,
        note
      );
      queryClient.invalidateQueries(["scan-values"]);
      queryClient.invalidateQueries(["rentals-available"]);
      onDone?.();
      onHide();
    } catch (e: any) {
      setError(e?.response?.data ?? e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal show onHide={onHide} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>
          {available === null
            ? `Set availability of ${count}`
            : `Mark ${count} ${available ? "available" : "unavailable"}`}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {initialAvailable === null && (
          <ButtonGroup className="mb-3">
            {[true, false].map((value) => (
              <ToggleButton
                key={String(value)}
                id={`availability-${value}`}
                type="radio"
                variant={value ? "outline-success" : "outline-secondary"}
                value={String(value)}
                checked={available === value}
                onChange={() => setAvailable(value)}
              >
                {value ? "Available for rent" : "Unavailable"}
              </ToggleButton>
            ))}
          </ButtonGroup>
        )}
        <div style={{ maxHeight: "35vh", overflowY: "auto" }} className="mb-2 small">
          <ul className="mb-0">
            {moons.map((m) => (
              <li key={m.id}>
                {m.name} <span className="text-muted">{m.place}</span>
              </li>
            ))}
          </ul>
        </div>
        <Form.Group>
          <Form.Label>Note (optional)</Form.Label>
          <Form.Control value={note} onChange={(e) => setNote(e.target.value)} />
        </Form.Group>
        <Form.Text>
          Availability applies once a moon isn&apos;t rented; it doesn&apos;t end current rentals.
        </Form.Text>
        {error && (
          <Alert variant="danger" className="mt-2 mb-0">
            {error}
          </Alert>
        )}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>
          Cancel
        </Button>
        <Button
          variant={available === false ? "secondary" : "success"}
          disabled={available === null || saving}
          onClick={save}
        >
          {available === false ? "Mark unavailable" : "Mark available"}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};
