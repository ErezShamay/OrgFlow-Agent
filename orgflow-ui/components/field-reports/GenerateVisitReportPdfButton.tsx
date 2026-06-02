"use client";

import { useEffect, useState } from "react";

import Button from "@/components/ui/Button";
import { useAuth } from "@/contexts/AuthContext";
import {
  downloadVisitReportPdf,
  type VisitReportPdfDownloadSource,
} from "@/lib/field-reports/pdf/generate-visit-report-pdf";
import type { PdfVisitReport } from "@/lib/field-reports/pdf/types";
import { hasVisitReportPdfLocally } from "@/lib/field-reports/pdf/visit-report-pdf-store";

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

  useEffect(() => {
    let active = true;

    void hasVisitReportPdfLocally(report.id).then((exists) => {
      if (active) {
        setHasCachedPdf(exists);
        onCacheChange?.(exists);
      }
    });

    return () => {
      active = false;
    };
  }, [report.id, onCacheChange]);

  const buttonLabel =
    label
    ?? (forceRegenerate
      ? "עדכן PDF"
      : hasCachedPdf
        ? "הורד PDF"
        : "הפק PDF");

  async function handleGenerate() {
    try {
      setLoading(true);
      const source = await downloadVisitReportPdf(
        {
          report,
          inspector: {
            full_name: profile?.full_name,
          },
        },
        { forceRegenerate }
      );
      setHasCachedPdf(true);
      onCacheChange?.(true);
      onComplete?.(source);
    } catch (error: unknown) {
      const message =
        error instanceof Error ? error.message : "הפקת PDF נכשלה";
      onError?.(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Button
      type="button"
      variant={variant}
      className={className}
      disabled={loading}
      onClick={() => void handleGenerate()}
    >
      {loading
        ? forceRegenerate
          ? "מעדכן PDF..."
          : hasCachedPdf
            ? "מוריד PDF..."
            : "מפיק PDF..."
        : buttonLabel}
    </Button>
  );
}
