/**
 * ברירות מחדל לבלוקי דוח - presets לפי visit_type וטקסטים קבועים (FR-0.4).
 */

import {
  constructionProgressTitleHe,
  defaultConstructionProgressRows,
  FINISHING_APARTMENT_FINDINGS_TITLE_HE,
  FINISHING_APARTMENTS_PROGRESS_TITLE_HE,
  FINISHING_LOBBY_FINDINGS_TITLE_HE,
  STRUCTURE_SITE_PROGRESS_TITLE_HE,
} from "../construction-progress";
import { DEFAULT_WINTER_RECOMMENDATIONS_HE } from "../pdf-block-defaults";
import { defaultFinishingChecklistBlock } from "./checklist-presets";
import type {
  ColumnPresetKey,
  FixedTextBlock,
  ProgressRow,
  ReportBlock,
  ReportBlockKind,
} from "./types";

/** visit_type משולב (FR-4.1) - קטלוג מלא + progress + findings. */
export const VISIT_TYPE_MIXED = "MIXED";

export const DEFAULT_NON_CONFORMANCE_DISCLAIMER_HE =
  'מלאכות שנמצאה לגביהן אי התאמה/הסתייגות מדווחות בגוף הדו"ח';

export const DEFAULT_SAFETY_DISCLAIMER_HE =
  "זו. היזם/הקבלן/ממונה הבטיחות אחראים למילוי כל הוראות הדין ביחס לבטיחות והוראות פיקוד העורף";

export { DEFAULT_WINTER_RECOMMENDATIONS_HE };

type BlockTemplate = {
  kind: ReportBlockKind;
  id: string;
  title_he: string;
  column_preset?: ColumnPresetKey;
  include_default_progress_rows?: boolean;
};

const STRUCTURE_SITE_BLOCK_TEMPLATES: readonly BlockTemplate[] = [
  {
    kind: "progress_table",
    id: "default-progress-table",
    title_he: STRUCTURE_SITE_PROGRESS_TITLE_HE,
    column_preset: "structure",
    include_default_progress_rows: true,
  },
  {
    kind: "findings_table",
    id: "default-findings-table",
    title_he: "ממצאים נוספים",
    column_preset: "simple",
  },
];

const FINISHING_APARTMENTS_BLOCK_TEMPLATES: readonly BlockTemplate[] = [
  {
    kind: "checklist",
    id: "default-finishing-checklist",
    title_he: FINISHING_APARTMENTS_PROGRESS_TITLE_HE,
  },
  {
    kind: "findings_table",
    id: "default-lobby-findings",
    title_he: FINISHING_LOBBY_FINDINGS_TITLE_HE,
    column_preset: "finishing",
  },
  {
    kind: "findings_table",
    id: "default-apartment-findings",
    title_he: FINISHING_APARTMENT_FINDINGS_TITLE_HE,
    column_preset: "finishing",
  },
];

const MIXED_BLOCK_TEMPLATES: readonly BlockTemplate[] = [
  {
    kind: "progress_table",
    id: "default-progress-table",
    title_he: "התקדמות הבנייה",
    column_preset: "progress",
    include_default_progress_rows: true,
  },
  {
    kind: "findings_table",
    id: "default-findings-table",
    title_he: "ממצאים / עבודות",
    column_preset: "rich",
  },
];

/** תבניות בלוקים לפי visit_type - ללא שורות ממצאים (rows ריק). */
export const DEFAULT_BLOCKS_BY_VISIT_TYPE: Record<
  string,
  readonly BlockTemplate[]
> = {
  STRUCTURE_SITE: STRUCTURE_SITE_BLOCK_TEMPLATES,
  FINISHING_APARTMENTS: FINISHING_APARTMENTS_BLOCK_TEMPLATES,
  [VISIT_TYPE_MIXED]: MIXED_BLOCK_TEMPLATES,
};

function progressRowsFromConstructionDefaults(visitType: string): ProgressRow[] {
  return defaultConstructionProgressRows(visitType).map((row, index) => ({
    id: `default-progress-row-${index}`,
    description: row.description,
    status: row.status,
    completion_date: row.completion_date,
    sort_order: index,
  }));
}

function materializeBlockTemplate(
  template: BlockTemplate,
  sortOrder: number,
  visitType: string
): ReportBlock {
  const base = {
    id: template.id,
    title_he: template.title_he,
    sort_order: sortOrder,
  };

  if (template.kind === "progress_table") {
    const rows =
      template.include_default_progress_rows === true
        ? progressRowsFromConstructionDefaults(visitType)
        : [];

    return {
      ...base,
      kind: "progress_table",
      column_preset: template.column_preset ?? "progress",
      rows,
    };
  }

  if (template.kind === "findings_table") {
    return {
      ...base,
      kind: "findings_table",
      column_preset: template.column_preset ?? "rich",
      rows: [],
    };
  }

  if (template.kind === "checklist") {
    return defaultFinishingChecklistBlock({
      id: template.id,
      title_he: template.title_he,
      sort_order: sortOrder,
    });
  }

  throw new Error(`Unsupported default block kind: ${template.kind}`);
}

/**
 * מחזיר בלוקי ברירת מחדל לדוח חדש לפי visit_type.
 * שורות התקדמות נלקחות מ-construction-progress; ממצאים ריקים.
 */
export function defaultReportBlocksForVisitType(visitType: string): ReportBlock[] {
  const templates = DEFAULT_BLOCKS_BY_VISIT_TYPE[visitType];
  if (!templates || templates.length === 0) {
    return [];
  }

  return templates.map((template, index) =>
    materializeBlockTemplate(template, index, visitType)
  );
}

/** כותרת ברירת מחדל לטבלת התקדמות - fallback כשאין preset ייעודי. */
export function defaultProgressBlockTitleHe(visitType: string): string {
  return constructionProgressTitleHe(visitType);
}

/** טקסטים קבועים (boilerplate) כמו בדוחות הלקוח - לשימוש ביצירת דוח חדש (FR-4.2). */
export function defaultFixedTextBlocks(): FixedTextBlock[] {
  return [
    {
      id: "default-non-conformance-disclaimer",
      kind: "non_conformance_disclaimer",
      body_he: DEFAULT_NON_CONFORMANCE_DISCLAIMER_HE,
      enabled: true,
      sort_order: 0,
    },
    {
      id: "default-safety-disclaimer",
      kind: "safety_disclaimer",
      body_he: DEFAULT_SAFETY_DISCLAIMER_HE,
      enabled: true,
      sort_order: 1,
    },
    {
      id: "default-winter-recommendations",
      kind: "winter_recommendations",
      title_he: "המלצות חורף / עונת גשמים",
      body_he: DEFAULT_WINTER_RECOMMENDATIONS_HE,
      enabled: false,
      sort_order: 2,
    },
  ];
}
