"use client";

import { useEffect, useRef, useState } from "react";

import Button from "@/components/ui/Button";
import VisitReportPdfPreviewDialog from "@/components/field-reports/VisitReportPdfPreviewDialog";
import { useAuth } from "@/contexts/AuthContext";
import {
  finalizeVisitReport,
  waitForFinalizeReportStatus,
} from "@/lib/field-reports/finalize-api";
import {
  downloadVisitReportPdf,
  generateVisitReportPdf,
  saveAndDownloadVisitReportPdf,
  buildPdfFilename,
  type VisitReportPdfDownloadSource,
} from "@/lib/field-reports/pdf/generate-visit-report-pdf";
import type { PdfVisitReport } from "@/lib/field-reports/pdf/types";
import {
  hasVisitReportPdfLocally,
  loadVisitReportPdfLocally,
  visitReportPdfStorageKey,
} from "@/lib/field-reports/pdf/visit-report-pdf-store";

type GenerateVisitReportPdfButtonProps = {
  report: PdfVisitReport;
  variant?: "primary" | "secondary";
  label?: string;
  className?: string;
  /** Regenerate from current report data and replace the single cached copy. */
  forceRegenerate?: boolean;
  serverReportId?: string | null;
  reportStatus?: string;
  canFinalize?: boolean;
  isOnline?: boolean;
  clientReportUuid?: string;
  onComplete?: (source: VisitReportPdfDownloadSource) => void;
  onError?: (message: string) => void;
  onCacheChange?: (hasCachedPdf: boolean) => void;
  onFinalizeStart?: () => void;
  onFinalizeComplete?: () => void;
  onFinalizeError?: (message: string) => void;
};

export default function GenerateVisitReportPdfButton({
  report,
  variant = "primary",
  label,
  className = "",
  forceRegenerate = false,
  serverReportId,
  reportStatus,
  canFinalize = false,
  isOnline = true,
  clientReportUuid,
  onComplete,
  onError,
  onCacheChange,
  onFinalizeStart,
  onFinalizeComplete,
  onFinalizeError,
}: GenerateVisitReportPdfButtonProps) {
  const { profile } = useAuth();
  const [loading, setLoading] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const [hasCachedPdf, setHasCachedPdf] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewConfirming, setPreviewConfirming] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState("");
  const previewBlobRef = useRef<Blob | null>(null);
  const pdfStorageKey = visitReportPdfStorageKey(report);

  const pdfInput = {
    report,
    inspector: {
      full_name: profile?.full_name,
    },
  };

  const needsFinalizePipeline =
    canFinalize
    && isOnline
    && Boolean(serverReportId?.trim())
    && (reportStatus === "CLOSED" || reportStatus === "FINALIZE_FAILED");

  const useCacheShortcut = !forceRegenerate && hasCachedPdf && !needsFinalizePipeline;

  useEffect(() => {
    let active = true;

    void hasVisitReportPdfLocally(pdfStorageKey).then((exists) => {
      if (active) {
        setHasCachedPdf(exists);
        onCacheChange?.(exists);
      }
    });

    return () => {
      active = false;
    };
  }, [pdfStorageKey, onCacheChange]);

  useEffect(() => {
    return () => {
      if (previewUrl?.startsWith("blob:")) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const buttonLabel =
    label
    ?? (finalizing
      ? "מעבד דוח..."
      : forceRegenerate
        ? "עדכן PDF"
        : useCacheShortcut
          ? "הורד PDF"
          : "הפק PDF");

  function clearPreviewState() {
    if (previewUrl?.startsWith("blob:")) {
      URL.revokeObjectURL(previewUrl);
    }
    previewBlobRef.current = null;
    setPreviewUrl(null);
    setPreviewError("");
    setPreviewLoading(false);
    setPreviewConfirming(false);
    setPreviewOpen(false);
  }

  async function triggerFinalize(blob: Blob) {
    const resolvedServerId = serverReportId?.trim() || null;
    const shouldFinalize =
      canFinalize
      && isOnline
      && resolvedServerId
      && (reportStatus === "CLOSED" || reportStatus === "FINALIZE_FAILED");

    if (!shouldFinalize) {
      return;
    }

    try {
      setFinalizing(true);
      onFinalizeStart?.();

      await finalizeVisitReport(
        resolvedServerId,
        {
          blob,
          filename: buildPdfFilename(report),
        },
        {
          clientReportUuid,
          idempotencyKey: clientReportUuid
            ? `finalize:${clientReportUuid}`
            : `finalize:${resolvedServerId}`,
        }
      );

      const result = await waitForFinalizeReportStatus(resolvedServerId);

      if (result.status === "FINALIZE_FAILED") {
        throw new Error("עיבוד הדוח נכשל — נסה שוב");
      }

      onFinalizeComplete?.();
    } catch (error: unknown) {
      const message =
        error instanceof Error ? error.message : "עיבוד הדוח נכשל";
      onFinalizeError?.(message);
      throw error;
    } finally {
      setFinalizing(false);
    }
  }

  async function openPreviewDialog() {
    setPreviewOpen(true);
    setPreviewLoading(true);
    setPreviewError("");

    if (previewUrl?.startsWith("blob:")) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    previewBlobRef.current = null;

    try {
      const blob = await generateVisitReportPdf(pdfInput);
      previewBlobRef.current = blob;
      setPreviewUrl(URL.createObjectURL(blob));
    } catch (error: unknown) {
      const message =
        error instanceof Error ? error.message : "הפקת תצוגה מקדימה נכשלה";
      setPreviewError(message);
      onError?.(message);
    } finally {
      setPreviewLoading(false);
    }
  }

  async function confirmPreview() {
    const blob = previewBlobRef.current;
    if (!blob) {
      return;
    }

    try {
      setPreviewConfirming(true);
      await saveAndDownloadVisitReportPdf(pdfInput, blob);
      setHasCachedPdf(true);
      onCacheChange?.(true);
      onComplete?.("generated");
      clearPreviewState();

      try {
        await triggerFinalize(blob);
      } catch (finalizeError: unknown) {
        const message =
          finalizeError instanceof Error
            ? finalizeError.message
            : "עיבוד הדוח נכשל";
        onError?.(message);
      }
    } catch (error: unknown) {
      const message =
        error instanceof Error ? error.message : "שמירת PDF נכשלה";
      setPreviewError(message);
      onError?.(message);
    } finally {
      setPreviewConfirming(false);
    }
  }

  async function handleGenerate() {
    try {
      setLoading(true);

      if (useCacheShortcut) {
        const cached = await loadVisitReportPdfLocally(pdfStorageKey);
        if (cached?.blob) {
          const source = await downloadVisitReportPdf(pdfInput);
          setHasCachedPdf(true);
          onCacheChange?.(true);
          onComplete?.(source);
          return;
        }
      }

      await openPreviewDialog();
    } catch (error: unknown) {
      const message =
        error instanceof Error ? error.message : "הפקת PDF נכשלה";
      onError?.(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Button
        type="button"
        variant={variant}
        className={className}
        disabled={loading || finalizing || previewOpen}
        onClick={() => void handleGenerate()}
      >
        {loading
          ? useCacheShortcut
            ? "מוריד PDF..."
            : "מכין תצוגה מקדימה..."
          : buttonLabel}
      </Button>

      <VisitReportPdfPreviewDialog
        open={previewOpen}
        loading={previewLoading}
        confirming={previewConfirming || finalizing}
        previewUrl={previewUrl}
        error={previewError}
        isRegenerate={forceRegenerate}
        onCancel={() => {
          if (!previewLoading && !previewConfirming && !finalizing) {
            clearPreviewState();
          }
        }}
        onConfirm={() => void confirmPreview()}
      />
    </>
  );
}
