const STORAGE_PREFIX = "orgflow-field-reports-editing";

export type FieldReportEditSession = {
  reportId: string;
  startedAt: string;
};

function storageKey(organizationId: string) {
  return `${STORAGE_PREFIX}:${organizationId}`;
}

export function readEditSession(
  organizationId: string
): FieldReportEditSession | null {
  if (typeof window === "undefined" || !organizationId) {
    return null;
  }

  const raw = localStorage.getItem(storageKey(organizationId));
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as FieldReportEditSession;
  } catch {
    return null;
  }
}

export function claimEditSession(
  organizationId: string,
  reportId: string
): FieldReportEditSession {
  const session: FieldReportEditSession = {
    reportId,
    startedAt: new Date().toISOString(),
  };

  localStorage.setItem(
    storageKey(organizationId),
    JSON.stringify(session)
  );

  return session;
}

export function releaseEditSession(
  organizationId: string,
  reportId: string
) {
  const current = readEditSession(organizationId);
  if (current?.reportId === reportId) {
    localStorage.removeItem(storageKey(organizationId));
  }
}

export function isEditingReport(
  organizationId: string,
  reportId: string
): boolean {
  return readEditSession(organizationId)?.reportId === reportId;
}

export function clearEditSession(organizationId: string) {
  if (typeof window === "undefined" || !organizationId) {
    return;
  }
  localStorage.removeItem(storageKey(organizationId));
}
