"use client";

import type { ReportBlockKind } from "@/lib/field-reports/schema/types";

export type ModularTemplateDraftBlock = {
  id: string;
  kind: ReportBlockKind;
  title_he: string;
  enabled: boolean;
  required: boolean;
};

export type ModularTemplateDraft = {
  templateId: string;
  templateLabel: string;
  visitType: string;
  name: string;
  examplePdf?: string;
  includeFixedTextBlocks: boolean;
  blocks: ModularTemplateDraftBlock[];
};

const STORAGE_PREFIX = "field-report:modular-template-draft:";

export function saveModularTemplateDraft(
  draft: ModularTemplateDraft
): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  const key = `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  try {
    window.sessionStorage.setItem(
      `${STORAGE_PREFIX}${key}`,
      JSON.stringify(draft)
    );
    return key;
  } catch {
    return null;
  }
}

export function readModularTemplateDraft(
  key: string
): ModularTemplateDraft | null {
  if (typeof window === "undefined" || !key) {
    return null;
  }

  try {
    const raw = window.sessionStorage.getItem(`${STORAGE_PREFIX}${key}`);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw) as ModularTemplateDraft;
    if (!parsed?.blocks?.length) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}
