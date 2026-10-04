import { postEndRental } from "../helpers/Api";
import { moonRental } from "../types";
import { useState } from "react";
import { Alert, Button, Form, Modal } from "react-bootstrap";
import { useQueryClient } from "react-query";

export const UnrentModal = ({ rental, onHide }: { rental: moonRental; onHide: () => void }) => {
  const queryClient = useQueryClient();
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const unrent = async () => {
    setSaving(true);
    setError(null);
    try {
      await postEndRental(rental.id, note.trim());
      queryClient.invalidateQueries(["rentals"]);
      queryClient.invalidateQueries(["scan-values"]);
      onHide();
    } catch (e: any) {
      setError(e?.response?.data ?? e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal show onHide={onHide}>
      <Modal.Header closeButton>
        <Modal.Title>Unrent {rental.moon.name}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <p className="mb-2">
          Ends the rental by {rental.contact.character_name} [{rental.corporation.corporation_name}]
          at {rental.price.toLocaleString()} ISK a month. The note and your name are added to the
          rental's notes.
        </p>
        <Form.Group>
          <Form.Label>Note (required)</Form.Label>
          <Form.Control
            as="textarea"
            rows={3}
            autoFocus
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Why is this rental ending?"
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
          Unrent
        </Button>
      </Modal.Footer>
    </Modal>
  );
};
