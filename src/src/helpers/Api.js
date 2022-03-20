import axios from "axios";
axios.defaults.xsrfHeaderName = "X-CSRFToken";

function fetchFromObject(obj, prop) {
  if (typeof obj === "undefined") return "Error";
  var _index = prop.indexOf(".");
  if (_index > -1) {
    return fetchFromObject(
      obj[prop.substring(0, _index)],
      prop.substr(_index + 1)
    );
  }
  return obj[prop];
}

function return_key_pair(label_key, value_key, ob) {
  return ob.reduce((p, c) => {
    try {
      p.push({
        value: fetchFromObject(c, value_key),
        label: fetchFromObject(c, label_key),
      });
      return p;
    } catch (err) {
      console.log(`ERROR searching for key/val`);
      console.log(err);
      return p;
    }
  }, []);
}

export async function searchChars(search_str) {
  const api = await axios.get(`/m/api/characters/search`, {
    params: { search_text: search_str },
  });
  const characters = return_key_pair(
    "character_name",
    "character_id",
    api.data
  );
  characters.sort();
  return characters;
}

export async function searchCorps(search_str) {
  const api = await axios.get(`/m/api/corporations/search`, {
    params: { search_text: search_str },
  });
  const corps = return_key_pair("corporation_name", "corporation_id", api.data);
  corps.sort();
  return corps;
}

export async function searchMoons(search_str) {
  const api = await axios.get(`/m/api/moons/search`, {
    params: { search_text: search_str },
  });
  const moons = return_key_pair("name", "id", api.data);
  moons.sort();
  return moons;
}

export async function getExtractions(days = 4) {
  const api = await axios.get(`/m/api/extractions`, {
    params: { past_days: days },
  });

  return api.data;
}
