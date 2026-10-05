// Moon names pasted one per line, e.g. "FM-JK5 IX - Moon 12". Spreadsheet rows keep only
// their first column. Blank lines and repeats are dropped.
export const parseMoonNames = (text: string): Array<string> => {
  const seen = new Set<string>();
  const names: Array<string> = [];
  text.split(/\r?\n/).forEach((line) => {
    const name = line.split("\t")[0].trim().replace(/\s+/g, " ");
    if (name && !seen.has(name.toLowerCase())) {
      seen.add(name.toLowerCase());
      names.push(name);
    }
  });
  return names;
};

export const moonKey = (name: string) => name.trim().replace(/\s+/g, " ").toLowerCase();
