import { openVisitReportPdfOnNative } from "@/lib/capacitor/visit-report-pdf-filesystem";

import {
  buildPdfFilename,
  buildVisitReportDocDefinition,
} from "./build-doc-definition";
import { createPdfPrinter } from "./font-loader";
import {
  resolveIllustrationDataUrl,
  resolveLinePhotos,
  resolveLogoDataUrl,
} from "./resolve-assets";
import type { VisitReportPdfInput } from "./types";
import {
  loadVisitReportPdfLocally,
  saveVisitReportPdfLocally,
  visitReportPdfStorageKey,
} from "./visit-report-pdf-store";
import { resolveVisitPdfIssueMarkers } from "./resolve-visit-pdf-issue-markers";

export type VisitReportPdfDownloadSource = "cache" | "generated";

export async function generateVisitReportPdf(
  input: VisitReportPdfInput
): Promise<Blob> {
  const pdfMake = await createPdfPrinter();
  const logoDataUrl = await resolveLogoDataUrl(
    input.logoDataUrl
      ?? input.report.organization_profile_snapshot?.logo_url
  );
  const illustrationDataUrl =
    input.illustrationDataUrl
    ?? (await resolveIllustrationDataUrl(input.report.header_fields || {}));
  const storageKey = visitReportPdfStorageKey(input.report);
  const linePhotos =
    input.linePhotos
    ?? (await resolveLinePhotos(storageKey, input.report.lines));
  const lineIssueMarkers =
    input.lineIssueMarkers
    ?? (await resolveVisitPdfIssueMarkers(input.report));

  const docDefinition = buildVisitReportDocDefinition({
    ...input,
    logoDataUrl,
    illustrationDataUrl,
    linePhotos,
    lineIssueMarkers,
  });

  try {
    const pdf = pdfMake.createPdf(docDefinition);
    // pdfmake 0.3+ returns a Promise; legacy callback style never resolves.
    return await pdf.getBlob();
  } catch (error) {
    throw error instanceof Error ? error : new Error("הפקת PDF נכשלה");
  }
}

export async function triggerVisitReportPdfDownload(
  reportId: string,
  blob: Blob,
  filename: string
): Promise<void> {
  const openedNative = await openVisitReportPdfOnNative(
    reportId,
    blob,
    filename
  );

  if (openedNative) {
    return;
  }

  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(objectUrl);
}

export async function saveAndDownloadVisitReportPdf(
  input: VisitReportPdfInput,
  blob: Blob
): Promise<void> {
  const filename = buildPdfFilename(input.report);
  const storageKey = visitReportPdfStorageKey(input.report);

  await saveVisitReportPdfLocally(
    storageKey,
    blob,
    filename,
    input.generatedAt ?? new Date()
  );
  await triggerVisitReportPdfDownload(storageKey, blob, filename);
}

export async function downloadVisitReportPdf(
  input: VisitReportPdfInput,
  options?: { forceRegenerate?: boolean }
): Promise<VisitReportPdfDownloadSource> {
  const filename = buildPdfFilename(input.report);
  const storageKey = visitReportPdfStorageKey(input.report);

  if (!options?.forceRegenerate) {
    const cached = await loadVisitReportPdfLocally(storageKey);
    if (cached?.blob) {
      await triggerVisitReportPdfDownload(
        storageKey,
        cached.blob,
        cached.filename || filename
      );
      return "cache";
    }
  }

  const blob = await generateVisitReportPdf(input);
  await saveAndDownloadVisitReportPdf(input, blob);
  return "generated";
}

export { buildPdfFilename, buildVisitReportDocDefinition };
