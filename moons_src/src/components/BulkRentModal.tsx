import { getScanProfiles, postNewRentals, searchChars, searchCorps } from "../helpers/Api";
import { taxProfile } from "../types";
import { ApiSelect } from "./ApiSelect";
import { useState } from "react";
import { Alert, Button, Form, Modal, Table } from "react-bootstrap";
import { useQuery, useQueryClient } from "react-query";

type Option = { label: string; value: number } | null;

// a moon to rent; suggested is null for moons without a scan, whose price must be typed
export interface RentItem {
  id: number;
  name: string;
  place: string;
  suggested: number | null;
}

export const rentItemFromValue = (m: {
  moon: { id: string | number; name: string };
  system: string;
  region: string;
  rent?: number;
}): RentItem => ({
  id: Number(m.moon.id),
  name: m.moon.name,
  place: `${m.system} - ${m.region}`,
  suggested: m.rent ?? null,
});

// rent several moons to one contact, each at its own (suggested) price; all or nothing
export const BulkRentModal = ({
  moons,
  onHide,
  onDone,
}: {
  moons: Array<RentItem>;
  onHide: () => void;
  onDone?: () => void;
}) => {
  const queryClient = useQueryClient();
  const [contact, setContact] = useState<Option>(null);
  const [corp, setCorp] = useState<Option>(null);
  const [note, setNote] = useState("");
  const [repriceMethodId, setRepriceMethodId] = useState<number | null>(null);
  const [prices, setPrices] = useState<Record<number, string>>(() =>
    Object.fromEntries(moons.map((m) => [m.id, m.suggested === null ? "" : String(m.suggested)]))
  );
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const profiles = useQuery(["scan-profiles"], () => getScanProfiles(), {
    refetchOnWindowFocus: false,
  });

  const priceOf = (m: RentItem) => prices[m.id];
  const pricesValid = moons.every((m) => priceOf(m) !== "" && Number(priceOf(m)) >= 0);
  const total = moons.reduce((sum, m) => sum + (Number(priceOf(m)) || 0), 0);

  const rent = async () => {
    setSaving(true);
    setError(null);
    try {
      await postNewRentals({
        contact_id: contact!.value,
        corporation_id: corp!.value,
        note,
        reprice_method_id: repriceMethodId,
        moons: moons.map((m) => ({ moon_id: m.id, price: Number(priceOf(m)) })),
      });
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
    <Modal show onHide={onHide} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Rent {moons.length} moons</Modal.Title>
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
          <Form.Label>Note</Form.Label>
          <Form.Control value={note} onChange={(e) => setNote(e.target.value)} />
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Label>Reprice with</Form.Label>
          <Form.Select
            value={repriceMethodId ?? ""}
            onChange={(e) => setRepriceMethodId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">Don&apos;t reprice</option>
            {(profiles.data ?? []).map((p: taxProfile) => (
              <option key={p.id} value={p.id}>
                {p.tag}
              </option>
            ))}
          </Form.Select>
        </Form.Group>
        <div style={{ maxHeight: "40vh", overflowY: "auto" }}>
          <Table size="sm" className="small mb-0 align-middle">
            <thead>
              <tr>
                <th>Moon</th>
                <th className="text-end">Suggested</th>
                <th style={{ width: 200 }}>Monthly price (ISK)</th>
              </tr>
            </thead>
            <tbody>
              {moons.map((m) => (
                <tr key={m.id}>
                  <td>
                    {m.name}
                    <div className="text-muted">{m.place}</div>
                  </td>
                  <td className="text-end">
                    {m.suggested === null ? (
                      <span className="text-muted">no scan</span>
                    ) : (
                      Math.round(m.suggested).toLocaleString()
                    )}
                  </td>
                  <td>
                    <Form.Control
                      size="sm"
                      type="number"
                      min={0}
                      value={priceOf(m)}
                      onChange={(e) => setPrices((p) => ({ ...p, [m.id]: e.target.value }))}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <th colSpan={2}>Total per month</th>
                <th>{total.toLocaleString()} ISK</th>
              </tr>
            </tfoot>
          </Table>
        </div>
        <Form.Text>
          Prices start at each moon&apos;s suggested rent; moons without a scan need a price. If any
          moon has been rented in the meantime, nothing is rented.
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
        <Button disabled={!contact || !corp || !pricesValid || saving} onClick={rent}>
          Rent {moons.length} moons
        </Button>
      </Modal.Footer>
    </Modal>
  );
};
