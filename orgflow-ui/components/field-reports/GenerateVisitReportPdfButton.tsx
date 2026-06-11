"use client";

import { useEffect, useRef, useState } from "react";

import Button from "@/components/ui/Button";
import VisitReportPdfPreviewDialog from "@/components/field-reports/VisitReportPdfPreviewDialog";
import { useAuth } from "@/contexts/AuthContext";
import {
  downloadVisitReportPdf,
  generateVisitReportPdf,
  saveAndDownloadVisitReportPdf,
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
  onComplete?: (source: VisitReportPdfDownloadSource) => void;
  onError?: (message: string) => void;
  onCacheChange?: (hasCachedPdf: boolean) => void;
};

export default function GenerateVisitReportPdfButton({
  report,
  variant = "primary",
  label,
  className = "",
  forceRegenerate = false,
  onComplete,
  onError,
  onCacheChange,
}: GenerateVisitReportPdfButtonProps) {
  const { profile } = useAuth();
  const [loading, setLoading] = useState(false);
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
    ?? (forceRegenerate
      ? "עדכן PDF"
      : hasCachedPdf
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

      if (!forceRegenerate) {
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
        disabled={loading || previewOpen}
        onClick={() => void handleGenerate()}
      >
        {loading
          ? forceRegenerate
            ? "מכין תצוגה מקדימה..."
            : hasCachedPdf
              ? "מוריד PDF..."
              : "מכין תצוגה מקדימה..."
          : buttonLabel}
      </Button>

      <VisitReportPdfPreviewDialog
        open={previewOpen}
        loading={previewLoading}
        confirming={previewConfirming}
        previewUrl={previewUrl}
        error={previewError}
        isRegenerate={forceRegenerate}
        onCancel={() => {
          if (!previewLoading && !previewConfirming) {
            clearPreviewState();
          }
        }}
        onConfirm={() => void confirmPreview()}
      />
    </>
  );
}
