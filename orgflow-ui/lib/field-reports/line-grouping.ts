/**
 * קיבוץ שורות ממצאים לפי דירה / קומה / אזור (FR-3.1).
 */

export type LineGroupKind = "none" | "apartment" | "floor" | "area";

export type LineGroupSelection = {
  kind: LineGroupKind;
  /** מספר דירה/קומה או שם אזור - ריק כש-kind הוא none. */
  value: string;
};

export const LINE_GROUP_KIND_OPTIONS: readonly {
  kind: LineGroupKind;
  label_he: string;
}[] = [
  { kind: "none", label_he: "ללא קיבוץ" },
  { kind: "apartment", label_he: "דירה" },
  { kind: "floor", label_he: "קומה" },
  { kind: "area", label_he: "אזור" },
] as const;

export function defaultLineGroupSelection(): LineGroupSelection {
  return { kind: "none", value: "" };
}

/** מפתח יציב לשמירה - e.g. `apartment:3`, `floor:2`, `area:מרפסות`. */
export function buildGroupKey(selection: LineGroupSelection): string | null {
  if (selection.kind === "none") {
    return null;
  }

  const value = selection.value.trim();
  if (!value) {
    return null;
  }

  return `${selection.kind}:${value}`;
}

/** תווית עברית ל-PDF ו-UI - e.g. `דירה 3`, `קומה 2`. */
export function buildGroupLabelHe(selection: LineGroupSelection): string | null {
  if (selection.kind === "none") {
    return null;
  }

  const value = selection.value.trim();
  if (!value) {
    return null;
  }

  switch (selection.kind) {
    case "apartment":
      return `דירה ${value}`;
    case "floor":
      return `קומה ${value}`;
    case "area":
      return value.startsWith("אזור") ? value : `אזור ${value}`;
    default:
      return null;
  }
}

export function lineGroupFieldsFromSelection(
  selection: LineGroupSelection
): { group_key: string | null; group_label_he: string | null } {
  return {
    group_key: buildGroupKey(selection),
    group_label_he: buildGroupLabelHe(selection),
  };
}

/** מפענח group_key שמור - לעריכת שורה קיימת. */
export function parseGroupKey(
  groupKey: string | null | undefined
): LineGroupSelection {
  if (!groupKey || typeof groupKey !== "string") {
    return defaultLineGroupSelection();
  }

  const separator = groupKey.indexOf(":");
  if (separator <= 0) {
    return defaultLineGroupSelection();
  }

  const kind = groupKey.slice(0, separator) as LineGroupKind;
  const value = groupKey.slice(separator + 1).trim();

  if (!value || !isLineGroupKind(kind)) {
    return defaultLineGroupSelection();
  }

  return { kind, value };
}

export function selectionFromLineGroupFields(line: {
  group_key?: string | null;
  group_label_he?: string | null;
}): LineGroupSelection {
  return parseGroupKey(line.group_key);
}

function isLineGroupKind(value: string): value is Exclude<LineGroupKind, "none"> {
  return value === "apartment" || value === "floor" || value === "area";
}
