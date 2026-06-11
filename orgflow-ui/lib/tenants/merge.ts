import type { Tenant } from "./types";

export type MergeReport = {
  merged: Tenant[];
  matched: number;
  unmatched: number;
  unmatchedContacts: { name: string; phone: string; email: string }[];
  unmatchedOwners: {
    name: string;
    apartment: string;
    building: string;
    entrance: string;
  }[];
};

function normApt(s: string): string {
  return (s || "").trim().replace(/^0+/, "").toLowerCase();
}

function normName(s: string): string {
  return (s || "")
    .trim()
    .replace(/["'׳״`.,-]/g, " ")
    .replace(/\s+/g, " ")
    .toLowerCase();
}

function nameTokens(s: string): string {
  return normName(s).split(" ").filter(Boolean).sort().join(" ");
}

function splitOwnerNames(name: string): string[] {
  const names = name
    .split(/[;,\n\r]+/)
    .map((part) => part.trim())
    .filter((part) => part && !/^[-–-\d\s]+$/.test(part));
  return names.length ? names : [name];
}

function tokenSet(s: string): Set<string> {
  return new Set(normName(s).split(" ").filter((t) => t.length >= 2));
}

export function mergeByOwnerName(
  apartments: Tenant[],
  contacts: Tenant[],
): MergeReport {
  const aByName = new Map<string, Tenant>();
  const aEntries: { tokens: Set<string>; row: Tenant }[] = [];

  for (const a of apartments) {
    for (const ownerName of splitOwnerNames(a.name)) {
      const n1 = normName(ownerName);
      const n2 = nameTokens(ownerName);
      const ownerRow = { ...a, name: ownerName };
      if (n1 && !aByName.has(n1)) aByName.set(n1, ownerRow);
      if (n2 && !aByName.has(n2)) aByName.set(n2, ownerRow);
      const ts = tokenSet(ownerName);
      if (ts.size > 0) aEntries.push({ tokens: ts, row: ownerRow });
    }
  }

  function fuzzyFind(name: string): Tenant | null {
    const ct = tokenSet(name);
    if (ct.size === 0) return null;
    let best: Tenant | null = null;
    let bestScore = 0;
    for (const e of aEntries) {
      let overlap = 0;
      for (const t of e.tokens) if (ct.has(t)) overlap++;
      if (overlap === 0) continue;
      const minSize = Math.min(e.tokens.size, ct.size);
      if (overlap < minSize) continue;
      if (overlap > bestScore) {
        bestScore = overlap;
        best = e.row;
      }
    }
    return best;
  }

  const matchedNames = new Set<string>();
  const merged: Tenant[] = [];
  const unmatchedContacts: MergeReport["unmatchedContacts"] = [];
  let matched = 0;

  for (const c of contacts) {
    const n1 = normName(c.name);
    const n2 = nameTokens(c.name);
    const a = aByName.get(n1) || aByName.get(n2) || fuzzyFind(c.name);
    if (a) {
      matchedNames.add(nameTokens(a.name));
      matched++;
    } else if (c.name || c.phone || c.email) {
      unmatchedContacts.push({
        name: c.name || "",
        phone: c.phone || "",
        email: c.email || "",
      });
    }
    merged.push({
      name: c.name || a?.name || "",
      phone: c.phone || "",
      email: c.email || "",
      apartment: a?.apartment || "",
      building: a?.building || "",
      entrance: a?.entrance || "",
    });
  }

  let unmatched = 0;
  const unmatchedOwners: MergeReport["unmatchedOwners"] = [];
  for (const a of apartments) {
    const key = nameTokens(a.name);
    if (!key || matchedNames.has(key)) continue;
    unmatched++;
    unmatchedOwners.push({
      name: a.name,
      apartment: a.apartment || "",
      building: a.building || "",
      entrance: a.entrance || "",
    });
    merged.push({ ...a });
  }

  merged.sort((x, y) => {
    const ax = parseInt(normApt(x.apartment), 10);
    const ay = parseInt(normApt(y.apartment), 10);
    if (!Number.isNaN(ax) && !Number.isNaN(ay) && ax !== ay) return ax - ay;
    const cmpApt = normApt(x.apartment).localeCompare(normApt(y.apartment));
    if (cmpApt !== 0) return cmpApt;
    const cmpB = (x.building || "").localeCompare(y.building || "");
    if (cmpB !== 0) return cmpB;
    const cmpE = (x.entrance || "").localeCompare(y.entrance || "");
    if (cmpE !== 0) return cmpE;
    return (x.name || "").localeCompare(y.name || "");
  });

  return { merged, matched, unmatched, unmatchedContacts, unmatchedOwners };
}

export function asContactRows(rows: Tenant[]): Tenant[] {
  return rows.map((row) => ({
    apartment: "",
    building: "",
    entrance: "",
    name: row.name,
    phone: row.phone,
    email: row.email,
  }));
}
