import { postEndRentals } from "../helpers/Api";
import { moonRental } from "../types";
import { useState } from "react";
import { Alert, Button, Form, Modal, Table } from "react-bootstrap";
import { useQueryClient } from "react-query";

const isk = (n: number) => `${Number(n).toLocaleString()} ISK`;

// one rental or many: all are unrented with the same note, or none are
export const UnrentModal = ({
  rentals,
  onHide,
  onDone,
}: {
  rentals: Array<moonRental>;
  onHide: () => void;
  onDone?: () => void;
}) => {
  const queryClient = useQueryClient();
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const single = rentals.length === 1;
  const total = rentals.reduce((sum, r) => sum + Number(r.price), 0);

  const unrent = async () => {
    setSaving(true);
    setError(null);
    try {
      await postEndRentals(
        rentals.map((r) => r.id),
        note.trim()
      );
      queryClient.invalidateQueries(["rentals"]);
      queryClient.invalidateQueries(["scan-values"]);
      onDone?.();
      onHide();
    } catch (e: any) {
      setError(e?.response?.data ?? e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal show onHide={onHide} size={single ? undefined : "lg"}>
      <Modal.Header closeButton>
        <Modal.Title>
          Unrent {single ? rentals[0].moon.name : `${rentals.length} moons`}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {single ? (
          <p className="mb-2">
            Ends the rental by {rentals[0].contact.character_name} [
            {rentals[0].corporation.corporation_name}] at {isk(rentals[0].price)} a month.
          </p>
        ) : (
          <div style={{ maxHeight: "40vh", overflowY: "auto" }} className="mb-2">
            <Table size="sm" className="small mb-0">
              <thead>
                <tr>
                  <th>Moon</th>
                  <th>Contact</th>
                  <th>Corporation</th>
                  <th className="text-end">Monthly</th>
                </tr>
              </thead>
              <tbody>
                {rentals.map((r) => (
                  <tr key={r.id}>
                    <td>{r.moon.name}</td>
                    <td>{r.contact.character_name}</td>
                    <td>{r.corporation.corporation_name}</td>
                    <td className="text-end">{isk(r.price)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <th colSpan={3}>Total</th>
                  <th className="text-end">{isk(total)}</th>
                </tr>
              </tfoot>
            </Table>
          </div>
        )}
        <Form.Text as="p" className="mt-0">
          The note and your name are added to {single ? "the rental's" : "each rental's"} notes.
          {!single && " If any of these has already ended, nothing is unrented."}
        </Form.Text>
        <Form.Group>
          <Form.Label>Note (required)</Form.Label>
          <Form.Control
            as="textarea"
            rows={3}
            autoFocus
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Why are these rentals ending?"
          />
        </Form.Group>
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
        <Button variant="danger" disabled={!note.trim() || saving} onClick={unrent}>
          Unrent {single ? "" : `${rentals.length} moons`}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};
