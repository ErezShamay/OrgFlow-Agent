import {
  deleteVisitReportPdfFromFilesystem,
  loadVisitReportPdfFromFilesystem,
  syncVisitReportPdfToFilesystem,
  useNativeVisitReportPdfFilesystem,
} from "@/lib/capacitor/visit-report-pdf-filesystem";
import {
  deleteReportPdfBlob,
  getReportPdfBlob,
  hasReportPdfBlob,
  saveReportPdfBlob,
  type StoredReportPdf,
} from "@/lib/field-reports/repositories/blobs-repository";

export type StoredVisitReportPdf = StoredReportPdf;

import { LEGACY_ORGFLOW_FIELD_REPORT_PDFS_DB } from "@/lib/elayoai/keys";

const LEGACY_DB_NAME = LEGACY_ORGFLOW_FIELD_REPORT_PDFS_DB;
const LEGACY_DB_VERSION = 1;
const LEGACY_STORE_NAME = "pdfs";

type LegacyStoredVisitReportPdf = {
  reportId: string;
  blob: Blob;
  filename: string;
  generatedAt: string;
};

function openLegacyDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === "undefined") {
      reject(new Error("IndexedDB is not available"));
      return;
    }

    const request = indexedDB.open(LEGACY_DB_NAME, LEGACY_DB_VERSION);

    request.onerror = () => {
      reject(request.error ?? new Error("Failed to open legacy PDF store"));
    };

    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(LEGACY_STORE_NAME)) {
        database.createObjectStore(LEGACY_STORE_NAME, { keyPath: "reportId" });
      }
    };

    request.onsuccess = () => {
      resolve(request.result);
    };
  });
}

async function loadLegacyVisitReportPdf(
  reportId: string
): Promise<LegacyStoredVisitReportPdf | null> {
  try {
    const database = await openLegacyDatabase();

    const record = await new Promise<LegacyStoredVisitReportPdf | null>(
      (resolve, reject) => {
        const transaction = database.transaction(LEGACY_STORE_NAME, "readonly");
        const store = transaction.objectStore(LEGACY_STORE_NAME);
        const request = store.get(reportId);

        request.onerror = () => {
          reject(request.error ?? new Error("Failed to load legacy visit report PDF"));
        };
        request.onsuccess = () => {
          resolve(
            (request.result as LegacyStoredVisitReportPdf | undefined) ?? null
          );
        };
      }
    );

    database.close();
    return record;
  } catch {
    return null;
  }
}

async function migrateLegacyPdfToBlobs(
  reportId: string,
  legacy: LegacyStoredVisitReportPdf
): Promise<StoredVisitReportPdf> {
  await saveReportPdfBlob(
    reportId,
    legacy.blob,
    legacy.filename || `${reportId}.pdf`,
    new Date(legacy.generatedAt)
  );
  return {
    reportId,
    blob: legacy.blob,
    filename: legacy.filename || `${reportId}.pdf`,
    generatedAt: legacy.generatedAt,
  };
}

/**
 * מפתח PDF - `client_report_uuid` (או מזהה נתיב כשאין עדיין דוח טעון).
 */
export function visitReportPdfStorageKey(
  report: { id: string; client_report_uuid?: string }
): string {
  return report.client_report_uuid || report.id;
}

export async function saveVisitReportPdfLocally(
  reportId: string,
  blob: Blob,
  filename: string,
  generatedAt: Date = new Date()
): Promise<void> {
  await saveReportPdfBlob(reportId, blob, filename, generatedAt);

  if (useNativeVisitReportPdfFilesystem()) {
    await syncVisitReportPdfToFilesystem(
      reportId,
      blob,
      filename,
      generatedAt
    );
  }
}

export async function loadVisitReportPdfLocally(
  reportId: string
): Promise<StoredVisitReportPdf | null> {
  const fromBlobs = await getReportPdfBlob(reportId);
  if (fromBlobs?.blob) {
    return fromBlobs;
  }

  const fromFilesystem = await loadVisitReportPdfFromFilesystem(reportId);
  if (fromFilesystem?.blob) {
    await saveReportPdfBlob(
      reportId,
      fromFilesystem.blob,
      fromFilesystem.filename,
      new Date(fromFilesystem.generatedAt)
    );
    return fromFilesystem;
  }

  const legacy = await loadLegacyVisitReportPdf(reportId);
  if (!legacy?.blob) {
    return null;
  }

  return migrateLegacyPdfToBlobs(reportId, legacy);
}

export async function hasVisitReportPdfLocally(
  reportId: string
): Promise<boolean> {
  if (await hasReportPdfBlob(reportId)) {
    return true;
  }

  if (useNativeVisitReportPdfFilesystem()) {
    const fromFilesystem = await loadVisitReportPdfFromFilesystem(reportId);
    if (fromFilesystem?.blob) {
      return true;
    }
  }

  const legacy = await loadLegacyVisitReportPdf(reportId);
  return Boolean(legacy?.blob);
}

export async function deleteVisitReportPdfLocally(
  reportId: string
): Promise<void> {
  await deleteReportPdfBlob(reportId);
  await deleteVisitReportPdfFromFilesystem(reportId);
}
