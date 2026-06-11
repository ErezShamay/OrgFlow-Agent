import { Capacitor } from "@capacitor/core";
import { Directory, Encoding, Filesystem } from "@capacitor/filesystem";

import { base64ToPdfBlob, blobToBase64 } from "@/lib/capacitor/blob-encoding";
import { isCapacitorNativePlatform } from "@/lib/capacitor/platform";
import type { StoredVisitReportPdf } from "@/lib/field-reports/pdf/visit-report-pdf-store";

const PDF_ROOT_DIR = "field-reports/pdfs";
const PDF_DATA_FILE = "report.pdf";
const PDF_META_FILE = "meta.json";

type PdfFilesystemMeta = {
  filename: string;
  generatedAt: string;
};

/** שמירת PDF ב-Filesystem ב-APK; ב-web - IndexedDB blobs בלבד. */
export function useNativeVisitReportPdfFilesystem(): boolean {
  return isCapacitorNativePlatform();
}

function reportPdfDirectory(reportId: string): string {
  return `${PDF_ROOT_DIR}/${reportId}`;
}

function reportPdfDataPath(reportId: string): string {
  return `${reportPdfDirectory(reportId)}/${PDF_DATA_FILE}`;
}

function reportPdfMetaPath(reportId: string): string {
  return `${reportPdfDirectory(reportId)}/${PDF_META_FILE}`;
}

export function sanitizeVisitReportPdfFilename(filename: string): string {
  const trimmed = filename.trim() || "visit-report.pdf";
  const safe = trimmed.replace(/[^\w.\-א-ת\s]/gu, "_").replace(/\s+/g, "_");

  return safe.toLowerCase().endsWith(".pdf") ? safe : `${safe}.pdf`;
}

/**
 * מעתיק PDF ל-Directory.Data (מראה ל-blobs - לפתיחה ב-viewer וגיבוי).
 */
export async function syncVisitReportPdfToFilesystem(
  reportId: string,
  blob: Blob,
  filename: string,
  generatedAt: Date = new Date()
): Promise<void> {
  if (!useNativeVisitReportPdfFilesystem()) {
    return;
  }

  const safeFilename = sanitizeVisitReportPdfFilename(filename);
  const base64 = await blobToBase64(blob);
  const meta: PdfFilesystemMeta = {
    filename: safeFilename,
    generatedAt: generatedAt.toISOString(),
  };

  await Filesystem.writeFile({
    path: reportPdfDataPath(reportId),
    data: base64,
    directory: Directory.Data,
    recursive: true,
  });

  await Filesystem.writeFile({
    path: reportPdfMetaPath(reportId),
    data: JSON.stringify(meta),
    directory: Directory.Data,
    encoding: Encoding.UTF8,
    recursive: true,
  });
}

export async function loadVisitReportPdfFromFilesystem(
  reportId: string
): Promise<StoredVisitReportPdf | null> {
  if (!useNativeVisitReportPdfFilesystem()) {
    return null;
  }

  try {
    const data = await Filesystem.readFile({
      path: reportPdfDataPath(reportId),
      directory: Directory.Data,
    });

    const base64 =
      typeof data.data === "string" ? data.data : "";
    if (!base64) {
      return null;
    }

    let filename = `${reportId}.pdf`;
    let generatedAt = new Date().toISOString();

    try {
      const metaFile = await Filesystem.readFile({
        path: reportPdfMetaPath(reportId),
        directory: Directory.Data,
        encoding: Encoding.UTF8,
      });
      const parsed = JSON.parse(
        String(metaFile.data)
      ) as PdfFilesystemMeta;
      if (parsed.filename) {
        filename = parsed.filename;
      }
      if (parsed.generatedAt) {
        generatedAt = parsed.generatedAt;
      }
    } catch {
      // meta אופציונלי
    }

    return {
      reportId,
      blob: base64ToPdfBlob(base64),
      filename,
      generatedAt,
    };
  } catch {
    return null;
  }
}

export async function deleteVisitReportPdfFromFilesystem(
  reportId: string
): Promise<void> {
  if (!useNativeVisitReportPdfFilesystem()) {
    return;
  }

  try {
    await Filesystem.rmdir({
      path: reportPdfDirectory(reportId),
      directory: Directory.Data,
      recursive: true,
    });
  } catch {
    // כבר נמחק
  }
}

/**
 * פתיחת PDF ב-native (לא `<a download>` - לא אמין ב-WebView).
 * Web: מחזיר false כדי שהקורא ישתמש ב-anchor download.
 */
export async function openVisitReportPdfOnNative(
  reportId: string,
  blob: Blob,
  filename: string
): Promise<boolean> {
  if (!useNativeVisitReportPdfFilesystem()) {
    return false;
  }

  await syncVisitReportPdfToFilesystem(reportId, blob, filename);

  const { uri } = await Filesystem.getUri({
    path: reportPdfDataPath(reportId),
    directory: Directory.Data,
  });

  const webUrl = Capacitor.convertFileSrc(uri);
  const opened = window.open(webUrl, "_blank", "noopener,noreferrer");

  if (!opened) {
    throw new Error(
      "לא הצלחנו לפתוח את ה-PDF. בדוק שהדפדפן במכשיר מאפשר חלונות קופצים."
    );
  }

  return true;
}
