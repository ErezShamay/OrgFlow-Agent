import { apiFetch } from "@/lib/api/client";

const STORAGE_PREFIX = "orgflow-field-reports-metadata-draft";

export type ReportMetadataDraft = {
  reportId: string;
  header_fields?: Record<string, unknown>;
  updatedAt: string;
};

function storageKey(organizationId: string) {
  return `${STORAGE_PREFIX}:${organizationId}`;
}

export function loadReportMetadataDrafts(
  organizationId: string
): ReportMetadataDraft[] {
  if (typeof window === "undefined" || !organizationId) {
    return [];
  }

  const raw = localStorage.getItem(storageKey(organizationId));
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw) as ReportMetadataDraft[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function getReportMetadataDraft(
  organizationId: string,
  reportId: string
): ReportMetadataDraft | null {
  return (
    loadReportMetadataDrafts(organizationId).find(
      (draft) => draft.reportId === reportId
    ) ?? null
  );
}

export function saveReportMetadataDraft(
  organizationId: string,
  reportId: string,
  header_fields: Record<string, unknown>
) {
  const existing = loadReportMetadataDrafts(organizationId).filter(
    (draft) => draft.reportId !== reportId
  );
  const draft: ReportMetadataDraft = {
    reportId,
    header_fields,
    updatedAt: new Date().toISOString(),
  };

  localStorage.setItem(
    storageKey(organizationId),
    JSON.stringify([...existing, draft])
  );

  return draft;
}

export async function flushReportMetadataDraft(
  organizationId: string,
  reportId: string
) {
  const draft = getReportMetadataDraft(organizationId, reportId);
  if (!draft?.header_fields) {
    return;
  }

  const response = await apiFetch(`/field-reports/visits/${reportId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ header_fields: draft.header_fields }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(
      payload.error?.message
        || payload.message
        || "סנכרון פרטי הדוח נכשל"
    );
  }

  clearReportMetadataDraft(organizationId, reportId);
}

export async function flushAllReportMetadataDrafts(
  organizationId: string
) {
  const drafts = loadReportMetadataDrafts(organizationId);

  for (const draft of drafts) {
    await flushReportMetadataDraft(organizationId, draft.reportId);
  }
}

export function clearReportMetadataDraft(
  organizationId: string,
  reportId: string
) {
  const remaining = loadReportMetadataDrafts(organizationId).filter(
    (draft) => draft.reportId !== reportId
  );

  if (remaining.length) {
    localStorage.setItem(
      storageKey(organizationId),
      JSON.stringify(remaining)
    );
  } else {
    localStorage.removeItem(storageKey(organizationId));
  }
}

export function clearAllReportMetadataDrafts(organizationId: string) {
  if (typeof window === "undefined" || !organizationId) {
    return;
  }
  localStorage.removeItem(storageKey(organizationId));
}
