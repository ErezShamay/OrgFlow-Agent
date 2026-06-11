import * as XLSX from "xlsx";

import type { Tenant } from "./types";

/**
 * Parse file A - the apartments/protocol file.
 * Each row represents ONE apartment with its owner name(s), apartment number,
 * building and entrance. Phone/email columns are ignored here even if present.
 * Owner names are NOT split - they're kept as written so the UI can display
 * "Cohen, Levy" together; splitting per-owner happens later in the merge step.
 */
export async function parseApartmentsExcel(file: File): Promise<Tenant[] | null> {
  const buffer = await file.arrayBuffer();
  const wb = XLSX.read(buffer, { type: "array" });

  for (const sheetName of wb.SheetNames) {
    const sheet = wb.Sheets[sheetName];
    const rows = XLSX.utils.sheet_to_json<unknown[]>(sheet, {
      header: 1,
      raw: false,
      defval: "",
    });
    if (rows.length < 2) continue;

    let headerIdx = -1;
    let headers: string[] = [];
    for (let i = 0; i < Math.min(rows.length, 15); i++) {
      const r = (rows[i] || []).map((c) => String(c ?? ""));
      const hasName =
        findCol(r, [
          "שםפרטי",
          "שםמשפחה",
          "שםמלא",
          "בעלתנכס",
          "בעלנכס",
          "שםהדייר",
          "דייר",
          "שם",
          "name",
          "firstname",
          "lastname",
        ]) !== -1;
      const hasApt =
        findCol(r, ["תתחלקה", "מסדירה", "מספרדירה", "דירה", "apartment", "apt", "unit"]) !== -1;
      if (hasName && hasApt) {
        headerIdx = i;
        headers = r;
        break;
      }
    }
    if (headerIdx === -1) continue;

    const colFirst = findCol(headers, ["שםפרטי", "firstname"]);
    const colLast = findCol(headers, ["שםמשפחה", "lastname", "surname"]);
    const colFull = findCol(headers, [
      "בעלתנכס",
      "בעלנכס",
      "שםמלא",
      "שםבעלהדירה",
      "שםהדייר",
      "דייר",
      "שם",
      "name",
    ]);
    const colApt = findCol(headers, [
      "תתחלקה",
      "מסדירה",
      "מספרדירה",
      "דירה",
      "apartment",
      "apt",
      "unit",
    ]);
    const colBuilding = findCol(headers, ["בניין", "בנין", "building"]);
    const colEntrance = findCol(headers, ["כניסה", "entrance"]);

    const tenants: Tenant[] = [];
    for (let i = headerIdx + 1; i < rows.length; i++) {
      const row = rows[i] || [];
      const get = (idx: number) => (idx >= 0 ? String(row[idx] ?? "").trim() : "");

      let name = "";
      if (colFirst !== -1 || colLast !== -1) {
        name = [get(colFirst), get(colLast)].filter(Boolean).join(" ").trim();
      }
      if (!name && colFull !== -1) name = get(colFull);

      const apartment = get(colApt);
      if (!name || !apartment) continue;

      tenants.push({
        apartment,
        name,
        phone: "",
        email: "",
        building: get(colBuilding),
        entrance: get(colEntrance),
      });
    }

    if (tenants.length > 0) return tenants;
  }
  return null;
}

/**
 * Parse file B - the contacts file.
 * Each owner may have several rows (one per phone/email), with the name and
 * apartment cells filled only on the first row (merged-cell pattern). We
 * forward-fill those values so every phone/email is attached to the right
 * owner. The apartment number from this file is treated as informational only;
 * the merge step uses the owner name as the join key (the apartment number in
 * file B is the OLD sub-parcel and must not override file A's apartment).
 */
export async function parseContactsExcel(file: File): Promise<Tenant[] | null> {
  const buffer = await file.arrayBuffer();
  const wb = XLSX.read(buffer, { type: "array" });

  for (const sheetName of wb.SheetNames) {
    const sheet = wb.Sheets[sheetName];
    const rows = XLSX.utils.sheet_to_json<unknown[]>(sheet, {
      header: 1,
      raw: false,
      defval: "",
    });
    if (rows.length < 2) continue;

    let headerIdx = -1;
    let headers: string[] = [];
    for (let i = 0; i < Math.min(rows.length, 15); i++) {
      const r = (rows[i] || []).map((c) => String(c ?? ""));
      const hasName =
        findCol(r, [
          "שםפרטי",
          "שםמשפחה",
          "שםמלא",
          "בעלתנכס",
          "בעלנכס",
          "שםהדייר",
          "דייר",
          "שם",
          "name",
          "firstname",
          "lastname",
        ]) !== -1;
      const hasContact =
        findCol(r, ["נייד", "טלפון", "phone", "mobile", "מייל", "email", "דואל", "אימייל"]) !== -1;
      if (hasName && hasContact) {
        headerIdx = i;
        headers = r;
        break;
      }
    }
    if (headerIdx === -1) continue;

    const colFirst = findCol(headers, ["שםפרטי", "firstname"]);
    const colLast = findCol(headers, ["שםמשפחה", "lastname", "surname"]);
    const colFull = findCol(headers, [
      "בעלתנכס",
      "בעלנכס",
      "שםמלא",
      "שםבעלהדירה",
      "שםהדייר",
      "דייר",
      "שם",
      "name",
    ]);
    const colApt = findCol(headers, [
      "תתחלקה",
      "מסדירה",
      "מספרדירה",
      "דירה",
      "apartment",
      "apt",
      "unit",
    ]);
    const colPhone = findCol(headers, ["נייד", "טלפוןנייד", "mobile", "טלפון", "phone"]);
    const colEmail = findCol(headers, ["מייל", "email", "דואל", "אימייל", "דואלקטרוני"]);

    const tenants: Tenant[] = [];
    let lastName = "";
    for (let i = headerIdx + 1; i < rows.length; i++) {
      const row = rows[i] || [];
      const get = (idx: number) => (idx >= 0 ? String(row[idx] ?? "").trim() : "");

      let name = "";
      if (colFirst !== -1 || colLast !== -1) {
        name = [get(colFirst), get(colLast)].filter(Boolean).join(" ").trim();
      }
      if (!name && colFull !== -1) name = get(colFull);

      const apartment = get(colApt);
      const phonesRaw = splitMulti(get(colPhone)).map(cleanPhone).filter(Boolean);
      const emailsRaw = splitMulti(get(colEmail)).filter((e) => e.includes("@"));

      // Skip blank rows entirely.
      if (!name && phonesRaw.length === 0 && emailsRaw.length === 0) continue;

      // Forward-fill the owner name when this row is just an extra phone/email
      // line for the previously seen owner.
      if (!name) name = lastName;
      else lastName = name;

      // Split multi-owner cells ("Cohen; Levy") so each owner gets their own row.
      const ownerNames = name
        .split(/[;,\n\r]+/)
        .map((p) => p.trim())
        .filter(Boolean);
      const finalNames = ownerNames.length ? ownerNames : [name];

      const count = Math.max(1, phonesRaw.length, emailsRaw.length);
      for (const ownerName of finalNames) {
        for (let k = 0; k < count; k++) {
          tenants.push({
            apartment, // informational only - merge uses name as join key
            name: ownerName,
            phone: phonesRaw[k] ?? "",
            email: emailsRaw[k] ?? "",
          });
        }
      }
    }

    if (tenants.length > 0) return tenants;
  }
  return null;
}

export async function parseExcelToText(file: File): Promise<string> {
  const buffer = await file.arrayBuffer();
  const wb = XLSX.read(buffer, { type: "array" });
  const lines: string[] = [];
  for (const sheetName of wb.SheetNames) {
    const sheet = wb.Sheets[sheetName];
    const csv = XLSX.utils.sheet_to_csv(sheet);
    lines.push(`--- גיליון: ${sheetName} ---`);
    lines.push(csv);
  }
  return lines.join("\n");
}

// Normalize a header cell for matching (strip spaces, quotes, punctuation).
function normHeader(s: unknown): string {
  return String(s ?? "")
    .replace(/["'`׳״]/g, "")
    .replace(/[/\\\-_.()]/g, "")
    .replace(/\s+/g, "")
    .trim()
    .toLowerCase();
}

// Find the index of the first column whose header matches any of the candidates.
function findCol(headers: string[], candidates: string[]): number {
  const normCands = candidates.map(normHeader);
  for (let i = 0; i < headers.length; i++) {
    const h = normHeader(headers[i]);
    if (!h) continue;
    if (normCands.some((c) => h === c || h.includes(c))) return i;
  }
  return -1;
}

function cleanPhone(s: string): string {
  const p = s.replace(/[^\d+]/g, "");
  if (!p) return "";
  // Excel often strips the leading 0 from Israeli numbers stored as numeric cells.
  // Restore it: 9 digits starting with 5 (mobile) → 05X..., 8 digits starting with
  // 2/3/4/8/9 (landline) → 0X...
  if (/^\+/.test(p)) return p;
  if (/^972/.test(p)) return "0" + p.slice(3);
  if (p.length === 9 && /^5/.test(p)) return "0" + p;
  if (p.length === 8 && /^[234689]/.test(p)) return "0" + p;
  return p;
}

function splitMulti(value: unknown): string[] {
  return String(value ?? "")
    .split(/[;,\n\r]+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

/**
 * Generic single-file Excel parser used by the standalone uploader (not the
 * merge flow). Recognizes any sheet that has a name column plus either an
 * apartment column or a contact column. The merge flow uses the dedicated
 * `parseApartmentsExcel` / `parseContactsExcel` functions instead.
 */
export async function tryParseExcelToTenants(file: File): Promise<Tenant[] | null> {
  const buffer = await file.arrayBuffer();
  const wb = XLSX.read(buffer, { type: "array" });

  for (const sheetName of wb.SheetNames) {
    const sheet = wb.Sheets[sheetName];
    const rows = XLSX.utils.sheet_to_json<unknown[]>(sheet, {
      header: 1,
      raw: false,
      defval: "",
    });
    if (rows.length < 2) continue;

    // Find the header row (first row containing recognizable columns near the top).
    let headerIdx = -1;
    let headers: string[] = [];
    for (let i = 0; i < Math.min(rows.length, 15); i++) {
      const r = (rows[i] || []).map((c) => String(c ?? ""));
      const hasName =
        findCol(r, [
          "שםפרטי",
          "שםמשפחה",
          "שםמלא",
          "בעלתנכס",
          "בעלנכס",
          "שםהדייר",
          "דייר",
          "שם",
          "name",
          "firstname",
          "lastname",
        ]) !== -1;
      const hasApt =
        findCol(r, ["תתחלקה", "מסדירה", "מספרדירה", "דירה", "apartment", "apt", "unit"]) !== -1;
      const hasContact =
        findCol(r, ["נייד", "טלפון", "phone", "mobile", "מייל", "email", "דואל", "אימייל"]) !== -1;
      const isHeader = (hasName || hasApt) && hasContact;
      if (isHeader) {
        headerIdx = i;
        headers = r;
        break;
      }
    }
    if (headerIdx === -1) continue;

    const colFirst = findCol(headers, ["שםפרטי", "firstname"]);
    const colLast = findCol(headers, ["שםמשפחה", "lastname", "surname"]);
    const colFull = findCol(headers, [
      "בעלתנכס",
      "בעלנכס",
      "שםמלא",
      "שםבעלהדירה",
      "שםהדייר",
      "דייר",
      "שם",
      "name",
    ]);
    const colApt = findCol(headers, [
      "תתחלקה",
      "מסדירה",
      "מספרדירה",
      "דירה",
      "apartment",
      "apt",
      "unit",
    ]);
    const colPhone = findCol(headers, ["נייד", "טלפוןנייד", "mobile", "טלפון", "phone"]);
    const colEmail = findCol(headers, ["מייל", "email", "דואל", "אימייל", "דואלקטרוני"]);

    const tenants: Tenant[] = [];
    // Forward-fill state: when an owner has several phone rows in Excel, the
    // name/apartment cells are usually filled only on the first row (or merged
    // cells), and the following rows arrive empty. Carry the last seen values
    // so every phone row is tied to the correct owner.
    let lastName = "";
    let lastApartment = "";
    for (let i = headerIdx + 1; i < rows.length; i++) {
      const row = rows[i] || [];
      const get = (idx: number) => (idx >= 0 ? String(row[idx] ?? "").trim() : "");

      let name = "";
      if (colFirst !== -1 || colLast !== -1) {
        name = [get(colFirst), get(colLast)].filter(Boolean).join(" ").trim();
      }
      if (!name && colFull !== -1) name = get(colFull);

      let apartment = get(colApt);
      const phonesRaw = splitMulti(get(colPhone)).map(cleanPhone).filter(Boolean);
      const emailsRaw = splitMulti(get(colEmail)).filter((e) => e.includes("@"));

      // Skip completely empty rows.
      if (!name && !apartment && phonesRaw.length === 0 && emailsRaw.length === 0) continue;

      // Inherit name/apartment from the previous non-empty owner row when this
      // row is just an extra phone/email line for the same owner.
      if (!name) name = lastName;
      else lastName = name;
      if (!apartment) apartment = lastApartment;
      else lastApartment = apartment;

      const count = Math.max(1, phonesRaw.length, emailsRaw.length);
      for (let k = 0; k < count; k++) {
        tenants.push({
          apartment,
          name,
          phone: phonesRaw[k] ?? phonesRaw[0] ?? "",
          email: emailsRaw[k] ?? emailsRaw[0] ?? "",
        });
      }
    }

    if (tenants.length > 0) return tenants;
  }

  return null;
}

