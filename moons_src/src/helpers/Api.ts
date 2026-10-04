import axios from "axios";
import Cookies from "js-cookie";

axios.defaults.xsrfHeaderName = "X-CSRFToken";

function fetchFromObject(obj: any, prop: any) {
  if (typeof obj === "undefined") return "Error";
  var _index = prop.indexOf(".");
  if (_index > -1) {
    return fetchFromObject(obj[prop.substring(0, _index)], prop.substr(_index + 1));
  }
  return obj[prop];
}

function return_key_pair(label_key: any, value_key: any, ob: any) {
  return ob.reduce((p: any, c: any) => {
    try {
      p.push({
        value: fetchFromObject(c, value_key),
        label: fetchFromObject(c, label_key),
      });
      return p;
    } catch {
      return p;
    }
  }, []);
}

export async function searchChars(search_str: any) {
  const api = await axios.get(`/m/api/characters/search`, {
    params: { search_text: search_str },
  });
  const characters = return_key_pair("character_name", "character_id", api.data);
  characters.sort();
  return characters;
}

export async function searchCorps(search_str: any) {
  const api = await axios.get(`/m/api/corporations/search`, {
    params: { search_text: search_str },
  });
  const corps = return_key_pair("corporation_name", "corporation_id", api.data);
  corps.sort();
  return corps;
}

export async function searchMoons(search_str: any) {
  const api = await axios.get(`/m/api/moons/search`, {
    params: { search_text: search_str },
  });
  const moons = return_key_pair("name", "id", api.data);
  moons.sort();
  return moons;
}

export async function getExtractions(days = 3) {
  const api = await axios.get(`/m/api/extractions`, {
    params: { past_days: days },
  });

  return api.data;
}

export async function getPastExtractions() {
  const api = await axios.get(`/m/api/extractions/past`);

  return api.data;
}

export async function getFutureExtractions() {
  const api = await axios.get(`/m/api/extractions/future`);

  return api.data;
}

export async function getPerms() {
  const api = await axios.get(`/m/api/user/permissions`);

  return api.data;
}

export async function getAdminList() {
  const api = await axios.get(`/m/api/admin/list`);

  return api.data;
}

export async function getAdminExplain() {
  const api = await axios.get(`/m/api/admin/explain`);

  return api.data;
}

export async function getAdminOutstanding() {
  const api = await axios.get(`/m/api/admin/outstanding`);

  return api.data;
}

export async function getRentals() {
  const api = await axios.get(`/m/api/rental/list`);

  return api.data;
}

// ninja's django_auth enforces CSRF on POST
const csrf = () => ({ headers: { "X-CSRFToken": Cookies.get("csrftoken") ?? "" } });

export async function postScanPreview(text: string) {
  const api = await axios.post(`/m/api/scans/preview`, { text }, csrf());

  return api.data;
}

export async function postScanImport(text: string) {
  const api = await axios.post(`/m/api/scans/import`, { text }, csrf());

  return api.data;
}

export async function getScanProfiles() {
  const api = await axios.get(`/m/api/scans/profiles`);

  return api.data;
}

export async function getScanRegions() {
  const api = await axios.get(`/m/api/scans/regions`);

  return api.data;
}

export async function getScanValues(taxRate: number, regionId: number) {
  const api = await axios.get(`/m/api/scans/values`, {
    params: { tax_rate: taxRate, region_id: regionId },
  });

  return api.data;
}

export async function getRentalSuggestion(moonId: number, taxRate: number) {
  const api = await axios.get(`/m/api/scans/suggestion`, {
    params: { moon_id: moonId, tax_rate: taxRate },
  });

  return api.data;
}

export async function postNewRental(rental: {
  moon_id: number;
  contact_id: number;
  corporation_id: number;
  price: number;
  note: string;
}) {
  const form = new URLSearchParams();
  Object.entries(rental).forEach(([k, v]) => form.append(k, String(v)));
  const api = await axios.post(`/m/api/rental/new`, form, csrf());

  return api.data;
}

export async function postEndRental(rentalId: number, note: string) {
  const form = new URLSearchParams();
  form.append("note", note);
  const api = await axios.post(`/m/api/rental/${rentalId}/end`, form, csrf());

  return api.data;
}
