import type { ReportBlockKind } from "@/lib/field-reports/schema/types";

import libraryData from "./template-library-data.json";

export type TemplateBlockSpec = {
  kind: ReportBlockKind;
  title_he: string;
  required?: boolean;
};

export type TemplateLibraryItem = {
  id: string;
  label_he: string;
  visitType: string;
  /** שם קובץ PDF לדוגמה מתוך docs/ */
  examplePdf?: string;
  blocks: TemplateBlockSpec[];
};

export type TemplateLibraryCategory = {
  id: string;
  title_he: string;
  items: TemplateLibraryItem[];
};

/** ספריית תבניות — תבנית ייעודית לכל PDF לדוגמה ב-docs. */
export const TEMPLATE_LIBRARY: TemplateLibraryCategory[] =
  libraryData as TemplateLibraryCategory[];

export function findTemplateLibraryItem(
  templateId: string
): TemplateLibraryItem | null {
  for (const category of TEMPLATE_LIBRARY) {
    const item = category.items.find((entry) => entry.id === templateId);
    if (item) {
      return item;
    }
  }
  return null;
}

export function modularBlocksFromTemplateItem(
  item: TemplateLibraryItem
): Array<{
  id: string;
  kind: ReportBlockKind;
  title_he: string;
  enabled: boolean;
  required: boolean;
}> {
  return item.blocks.map((block, index) => ({
    id: `${item.id}-${block.kind}-${index}`,
    kind: block.kind,
    title_he: block.title_he,
    enabled: true,
    required: Boolean(block.required),
  }));
}

export function countTemplateLibraryItems(): number {
  return TEMPLATE_LIBRARY.reduce(
    (total, category) => total + category.items.length,
    0
  );
}
