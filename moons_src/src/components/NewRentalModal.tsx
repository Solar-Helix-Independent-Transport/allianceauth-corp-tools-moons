import {
  getRentalSuggestion,
  getScanProfiles,
  postNewRental,
  searchChars,
  searchCorps,
  searchMoons,
} from "../helpers/Api";
import { taxProfile } from "../types";
import { ApiSelect } from "./ApiSelect";
import { useState } from "react";
import { Alert, Button, Form, Modal } from "react-bootstrap";
import { useQuery, useQueryClient } from "react-query";

type Option = { label: string; value: number } | null;

const PROFILE_KEY = "moons-rental-suggestion-profile";

const rememberedProfile = () => {
  try {
    return Number(localStorage.getItem(PROFILE_KEY)) || null;
  } catch {
    return null;
  }
};

export const NewRentalModal = ({
  show,
  onHide,
  initialMoon = null,
  initialPrice,
  initialProfileId,
}: {
  show: boolean;
  onHide: () => void;
  // prefilled when renting from Moon Values
  initialMoon?: Option;
  initialPrice?: number;
  initialProfileId?: number;
}) => {
  const queryClient = useQueryClient();
  const [contact, setContact] = useState<Option>(null);
  const [corp, setCorp] = useState<Option>(null);
  const [moon, setMoon] = useState<Option>(initialMoon);
  const [price, setPrice] = useState(initialPrice !== undefined ? String(initialPrice) : "");
  const [note, setNote] = useState("");
  const [profileId, setProfileId] = useState<number | null>(initialProfileId ?? rememberedProfile);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const profiles = useQuery(["scan-profiles"], () => getScanProfiles(), {
    enabled: show,
    refetchOnWindowFocus: false,
  });
  const offered: Array<taxProfile> = profiles.data ?? [];
  const selected = offered.find((p) => p.id === profileId)?.id ?? offered[0]?.id;

  const suggestion = useQuery(
    ["rental-suggestion", moon?.value, selected],
    () => getRentalSuggestion(moon!.value, selected!),
    { enabled: show && !!moon && selected !== undefined, refetchOnWindowFocus: false }
  );

  const pickProfile = (id: number) => {
    setProfileId(id);
    try {
      localStorage.setItem(PROFILE_KEY, String(id));
    } catch {
      // remembering the choice is a convenience only
    }
  };

  const create = async () => {
    setSaving(true);
    setError(null);
    try {
      await postNewRental({
        moon_id: moon!.value,
        contact_id: contact!.value,
        corporation_id: corp!.value,
        price: Number(price),
        note,
      });
      queryClient.invalidateQueries(["rentals"]);
      queryClient.invalidateQueries(["scan-values"]);
      onHide();
    } catch (e: any) {
      setError(e?.response?.data ?? e.message);
    } finally {
      setSaving(false);
    }
  };

  const suggested: number | null | undefined = suggestion.data?.price;

  return (
    <Modal show={show} onHide={onHide}>
      <Modal.Header closeButton>
        <Modal.Title>New Moon Rental</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form.Group className="mb-2">
          <Form.Label>Contact character</Form.Label>
          <ApiSelect apiLookup={searchChars} setValue={setContact} />
        </Form.Group>
        <Form.Group className="mb-2">
          <Form.Label>Corporation</Form.Label>
          <ApiSelect apiLookup={searchCorps} setValue={setCorp} />
        </Form.Group>
        <Form.Group className="mb-2">
          <Form.Label>Moon</Form.Label>
          <ApiSelect apiLookup={searchMoons} setValue={setMoon} defaultValue={initialMoon} />
        </Form.Group>
        <Form.Group className="mb-2">
          <Form.Label>Note</Form.Label>
          <Form.Control value={note} onChange={(e) => setNote(e.target.value)} />
        </Form.Group>
        <Form.Group className="mb-2">
          <Form.Label>Monthly price (ISK)</Form.Label>
          <Form.Control
            type="number"
            min={0}
            value={price}
            onChange={(e) => setPrice(e.target.value)}
          />
        </Form.Group>
        {moon && offered.length > 0 && suggested !== null && (
          <div className="d-flex gap-2 align-items-center small">
            Suggested under
            <Form.Select
              size="sm"
              style={{ width: 200 }}
              value={selected}
              onChange={(e) => pickProfile(Number(e.target.value))}
            >
              {offered.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.tag}
                </option>
              ))}
            </Form.Select>
            {suggested !== undefined && (
              <>
                <strong>{suggested.toLocaleString()} ISK</strong>
                <Button
                  size="sm"
                  variant="outline-primary"
                  onClick={() => setPrice(String(suggested))}
                >
                  Use
                </Button>
              </>
            )}
          </div>
        )}
        {moon && !!suggestion.error && (
          <div className="small text-danger">
            No suggestion:{" "}
            {(suggestion.error as any)?.response?.data ?? (suggestion.error as Error).message}
          </div>
        )}
        {moon && suggested === null && (
          <div className="small text-muted">No scan for this moon — no suggestion.</div>
        )}
        {error && (
          <Alert variant="danger" className="mt-2 mb-0">
            {error}
          </Alert>
        )}
      </Modal.Body>
      <Modal.Footer>
        <Button disabled={!contact || !corp || !moon || !price || saving} onClick={create}>
          Create
        </Button>
      </Modal.Footer>
    </Modal>
  );
};
