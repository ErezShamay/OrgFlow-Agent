"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  startTransition,
  useCallback,
  useEffect,
  useState,
} from "react";

import FinishReportDialog, {
  type ClosePreview,
} from "@/components/field-reports/FinishReportDialog";
import CancelReportCreationDialog from "@/components/field-reports/CancelReportCreationDialog";
import DeleteReportDialog from "@/components/reports/DeleteReportDialog";
import VisitReportAlerts from "@/components/field-reports/VisitReportAlerts";
import VisitReportPdfActions, {
  shouldShowVisitReportPdfActions,
} from "@/components/field-reports/VisitReportPdfActions";
import VisitReportPrimaryActions from "@/components/field-reports/VisitReportPrimaryActions";
import VisitReportEditor from "@/components/field-reports/VisitReportEditor";
import VisitReportIssueDiffPanel from "@/components/quality-issues/VisitReportIssueDiffPanel";
import Button from "@/components/ui/Button";
import { useAuth } from "@/contexts/AuthContext";
import { useEffectiveRole } from "@/hooks/useEffectiveRole";
import { useFieldReportDataSource } from "@/hooks/useFieldReportDataSource";
import { useFieldReportEditSession } from "@/hooks/useFieldReportEditSession";
import { useFieldReportModule } from "@/hooks/useFieldReportModule";
import { apiFetch } from "@/lib/api/client";
import {
  fieldReportDataSourceModeLabelHe,
} from "@/lib/field-reports/data-source";
import { finishLocalVisitReportWithPdf } from "@/lib/field-reports/close-local-visit-report";
import { discardLocalVisitReport } from "@/lib/field-reports/discard-local-visit-report";
import { canFinalizeFieldReports } from "@/lib/field-reports/publish-access";
import { visitReportPipelineStatusLabel } from "@/lib/field-reports/finalize-status-labels";
import {
  buildSupervisionClosePreview,
  isSupervisionVisitReport,
  prepareSupervisionReportForClose,
  SupervisionCloseValidationError,
} from "@/lib/field-reports/supervision-close";
import {
  clientVisitReportUuid,
  loadVisitReportForPage,
  localVisitReportToView,
  serverVisitReportId,
  type VisitReportView,
} from "@/lib/field-reports/visit-report-view";
import { buildClosePreview } from "@/lib/field-reports/close-preview";
import { downloadVisitReportPdf } from "@/lib/field-reports/pdf/generate-visit-report-pdf";
import {
  hasVisitReportPdfLocally,
} from "@/lib/field-reports/pdf/visit-report-pdf-store";
import type { OrganizationProfileSnapshot } from "@/lib/field-reports/pdf/types";
import {
  fieldReportDetailPath,
  projectFieldReportsListPath,
  resolveFieldReportRouteId,
} from "@/lib/field-reports/routes";
import { shouldShowVisitIssueDiff } from "@/lib/quality-issues/visit-issue-diff";
import {
  deleteFieldVisitReport,
  fetchFieldVisitReportDeleteEligibility,
} from "@/lib/reports/delete-report-api";
import { useOffline } from "@/providers/OfflineProvider";
import { toast } from "sonner";

type VisitReport = VisitReportView & {
  organization_profile_snapshot?: OrganizationProfileSnapshot | null;
};

export default function FieldVisitReportPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const paramId = typeof params.id === "string" ? params.id : "";
  const reportId = resolveFieldReportRouteId(paramId, searchParams);
  const { status: moduleStatus } = useFieldReportModule();
  const organizationId = moduleStatus?.organization_id || "";
  const { isOnline } = useOffline();
  const { profile } = useAuth();
  const effectiveRole = useEffectiveRole();
  const canFinalizeReport = canFinalizeFieldReports(effectiveRole);
  const editSession = useFieldReportEditSession(
    organizationId,
    reportId
  );
  const [report, setReport] = useState<VisitReport | null>(null);
  const [dataSourceContext, setDataSourceContext] = useState({
    hasLocalReport: false,
    serverReportId: null as string | null,
  });
  const [hasLocalRecord, setHasLocalRecord] = useState(false);
  const {
    mode: dataSourceMode,
    pinging,
    network,
    useLocalReports,
    canCallVisitReportApi,
  } = useFieldReportDataSource(dataSourceContext);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [finishOpen, setFinishOpen] = useState(false);
  const [finishLoading, setFinishLoading] = useState(false);
  const [finishError, setFinishError] = useState("");
  const [closePreview, setClosePreview] = useState<ClosePreview | null>(
    null
  );
  const [pdfError, setPdfError] = useState("");
  const [pdfNotice, setPdfNotice] = useState("");
  const [hasLocalPdf, setHasLocalPdf] = useState(false);
  const [reopenLoading, setReopenLoading] = useState(false);
  const [reopenError, setReopenError] = useState("");
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [cancelLoading, setCancelLoading] = useState(false);
  const [cancelError, setCancelError] = useState("");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const [deleteEligible, setDeleteEligible] = useState(false);

  const isReopenedForEdit = Boolean(
    report?.is_editable && report?.was_closed
  );
  const canCloseOffline =
    useLocalReports || dataSourceContext.hasLocalReport;

  const loadReport = useCallback(async () => {
    if (!reportId) {
      setLoading(false);
      setError("מזהה דוח חסר");
      setReport(null);
      return;
    }

    try {
      setLoading(true);
      setError("");

      const loaded = await loadVisitReportForPage(reportId, network);

      setReport(loaded.report as VisitReport);
      setHasLocalRecord(Boolean(loaded.localRecord));
      setDataSourceContext({
        hasLocalReport: Boolean(loaded.localRecord),
        serverReportId: loaded.report.server_report_id ?? null,
      });
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "טעינת הדוח נכשלה"
      );
    } finally {
      setLoading(false);
    }
  }, [reportId, network]);

  useEffect(() => {
    startTransition(() => {
      void loadReport();
    });
  }, [loadReport]);

  useEffect(() => {
    function handleSyncComplete() {
      void loadReport();
    }

    window.addEventListener(
      "field-report-sync-complete",
      handleSyncComplete
    );
    return () => {
      window.removeEventListener(
        "field-report-sync-complete",
        handleSyncComplete
      );
    };
  }, [loadReport]);

  const pdfStorageKey = report
    ? clientVisitReportUuid(report)
    : reportId;

  useEffect(() => {
    if (!pdfStorageKey) {
      return;
    }

    let active = true;

    void hasVisitReportPdfLocally(pdfStorageKey).then((exists) => {
      if (active) {
        setHasLocalPdf(exists);
      }
    });

    return () => {
      active = false;
    };
  }, [pdfStorageKey, report?.status]);

  useEffect(() => {
    const serverId = report ? serverVisitReportId(report) : null;
    if (!serverId || !canCallVisitReportApi) {
      setDeleteEligible(false);
      return;
    }

    let active = true;

    void fetchFieldVisitReportDeleteEligibility(serverId)
      .then((eligibility) => {
        if (active) {
          setDeleteEligible(eligibility.deletable);
        }
      })
      .catch(() => {
        if (active) {
          setDeleteEligible(false);
        }
      });

    return () => {
      active = false;
    };
  }, [report, canCallVisitReportApi]);

  async function openFinishDialog() {
    if (!report?.is_editable) {
      return;
    }

    setFinishOpen(true);
    setFinishError("");
    setFinishLoading(true);

    const supervisionReport = isSupervisionVisitReport(
      report.header_fields,
      report.visit_type
    );

    const localPreview = supervisionReport
      ? buildSupervisionClosePreview({
          header_fields: report.header_fields,
          visit_type: report.visit_type,
          lines: report.lines,
        })
      : buildClosePreview(report.lines);
    setClosePreview(localPreview);

    if (!isOnline || supervisionReport) {
      setFinishLoading(false);
      return;
    }

    try {
      const serverId = serverVisitReportId(report);
      if (!serverId) {
        setFinishLoading(false);
        return;
      }

      const response = await apiFetch(
        `/field-reports/visits/${serverId}/close-preview`
      );

      if (response.ok) {
        setClosePreview(await response.json());
      }
    } catch {
      // Keep local preview when the server check fails.
    } finally {
      setFinishLoading(false);
    }
  }

  function navigateAfterFinishReport(finishedReport: VisitReport) {
    const projectId = finishedReport.project_id?.trim();
    router.push(
      projectId
        ? projectFieldReportsListPath(projectId)
        : "/field-reports"
    );
  }

  async function confirmFinishReport() {
    if (!report?.is_editable) {
      return;
    }

    const serverId = serverVisitReportId(report);
    const closeLocally =
      useLocalReports || dataSourceContext.hasLocalReport;
    const supervisionReport = isSupervisionVisitReport(
      report.header_fields,
      report.visit_type
    );

    try {
      setFinishLoading(true);
      setFinishError("");

      if (closeLocally) {
        let reportForClose = report;

        if (supervisionReport) {
          const prepared = await prepareSupervisionReportForClose(
            clientVisitReportUuid(report)
          );
          reportForClose = localVisitReportToView(prepared) as VisitReport;
          setReport(reportForClose);
        }

        const { view, pdfSource } = await finishLocalVisitReportWithPdf({
          report: reportForClose,
          inspector: { full_name: profile?.full_name },
        });

        setReport(view as VisitReport);
        setFinishOpen(false);
        editSession.release();
        setPdfError("");
        setHasLocalPdf(true);
        setPdfNotice(
          pdfSource === "cache"
            ? "הדוח נסגר במכשיר. ה-PDF כבר היה שמור."
            : "הדוח נסגר במכשיר וה-PDF נשמר."
        );

        if (canCallVisitReportApi && serverId && isOnline) {
          try {
            const response = await apiFetch(
              `/field-reports/visits/${serverId}/close`,
              { method: "POST" }
            );

            if (response.ok) {
              const closed = (await response.json()) as VisitReport;
              setReport({
                ...closed,
                client_report_uuid: clientVisitReportUuid(view),
                server_report_id: serverId,
              });
            }
          } catch {
            // סגירה מקומית היא מקור האמת בשטח; סנכרון יושלם בתור הסנכרון.
          }
        }

        navigateAfterFinishReport(view as VisitReport);
        return;
      }

      if (!isOnline) {
        setFinishError("סגירת דוח דורשת חיבור לרשת");
        return;
      }

      if (!serverId) {
        setFinishError("דוח לא נמצא בשרת");
        return;
      }

      const response = await apiFetch(
        `/field-reports/visits/${serverId}/close`,
        { method: "POST" }
      );

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(
          payload.error?.message
            || payload.message
            || "סגירת הדוח נכשלה"
        );
      }

      const closed = (await response.json()) as VisitReport;
      setReport(closed);
      setFinishOpen(false);
      editSession.release();
      setPdfNotice("");
      setPdfError("");

      try {
        const source = await downloadVisitReportPdf({
          report: closed,
          inspector: { full_name: profile?.full_name },
        });
        setHasLocalPdf(true);
        setPdfNotice(
          source === "cache"
            ? "הדוח נסגר וה-PDF הורד מהעותק השמור במכשיר."
            : "הדוח נסגר, ה-PDF נשמר במכשיר והורד."
        );
      } catch (pdfErr: unknown) {
        setPdfError(
          pdfErr instanceof Error
            ? pdfErr.message
            : "הדוח נסגר אך הפקת PDF נכשלה - נסה שוב מהכפתור למטה."
        );
      }

      navigateAfterFinishReport(closed);
    } catch (err: unknown) {
      if (err instanceof SupervisionCloseValidationError) {
        setClosePreview((current) => ({
          line_count: current?.line_count ?? report?.lines.length ?? 0,
          empty_line_count: current?.empty_line_count ?? 0,
          empty_line_ids: current?.empty_line_ids ?? [],
          catalog_warning_count: current?.catalog_warning_count ?? 0,
          warnings: current?.warnings ?? [],
          blocking_errors: err.errors.map((entry) => entry.message),
        }));
      }

      setFinishError(
        err instanceof Error ? err.message : "סגירת הדוח נכשלה"
      );
    } finally {
      setFinishLoading(false);
    }
  }

  async function confirmCancelReport() {
    if (!report || !organizationId) {
      return;
    }

    try {
      setCancelLoading(true);
      setCancelError("");

      await discardLocalVisitReport({
        organizationId,
        clientReportUuid: clientVisitReportUuid(report),
        serverReportId: serverVisitReportId(report),
      });
      editSession.release();
      setCancelDialogOpen(false);

      const projectId = report.project_id?.trim();
      router.push(
        projectId
          ? `/projects/${encodeURIComponent(projectId)}`
          : "/field-reports"
      );
    } catch (err: unknown) {
      setCancelError(
        err instanceof Error ? err.message : "ביטול הדוח נכשל"
      );
    } finally {
      setCancelLoading(false);
    }
  }

  async function confirmDeleteReport() {
    if (!report || !organizationId) {
      return;
    }

    try {
      setDeleteLoading(true);
      setDeleteError("");

      const serverId = serverVisitReportId(report);
      if (serverId && canCallVisitReportApi) {
        await deleteFieldVisitReport(serverId);
      }

      await discardLocalVisitReport({
        organizationId,
        clientReportUuid: clientVisitReportUuid(report),
        serverReportId: serverId,
      });
      editSession.release();
      setDeleteDialogOpen(false);
      toast.success("הדוח נמחק");

      const projectId = report.project_id?.trim();
      router.push(
        projectId
          ? `/projects/${encodeURIComponent(projectId)}`
          : "/field-reports"
      );
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "מחיקת הדוח נכשלה";
      setDeleteError(message);
      toast.error(message);
    } finally {
      setDeleteLoading(false);
    }
  }

  async function confirmReopenReport() {
    if (!report?.can_reopen) {
      return;
    }

    if (!isOnline) {
      setReopenError("עריכה מחדש דורשת חיבור לרשת");
      return;
    }

    try {
      setReopenLoading(true);
      setReopenError("");

      const serverId = serverVisitReportId(report);
      if (!serverId) {
        setReopenError("פתיחה מחדש דורשת דוח שסונכרן לשרת");
        return;
      }

      const response = await apiFetch(
        `/field-reports/visits/${serverId}/reopen`,
        { method: "POST" }
      );

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(
          payload.error?.message
            || payload.message
            || "פתיחת הדוח לעריכה נכשלה"
        );
      }

      const reopened = (await response.json()) as VisitReport;
      setReport(reopened);
      editSession.claim();
      setPdfNotice("");
      setPdfError("");
    } catch (err: unknown) {
      setReopenError(
        err instanceof Error
          ? err.message
          : "פתיחת הדוח לעריכה נכשלה"
      );
    } finally {
      setReopenLoading(false);
    }
  }

  function handleFinalizeStart() {
    if (!report) {
      return;
    }
    setReport({
      ...report,
      status: "FINALIZING",
      status_label_he: "מעבד...",
      is_editable: false,
    });
  }

  function handleFinalizeComplete() {
    void loadReport();
    window.dispatchEvent(new CustomEvent("field-report-sync-complete"));
  }

  if (loading) {
    return (
      <div className="of-container mx-auto w-full max-w-5xl p-4 text-sm text-zinc-500 md:p-6 lg:p-8">
        טוען דוח...
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="of-container mx-auto w-full max-w-5xl space-y-4 p-4 md:p-6 lg:p-8">
        <p className="text-sm text-red-600">{error || "דוח לא נמצא"}</p>
        <Button variant="secondary" onClick={() => void loadReport()}>
          נסה שוב
        </Button>
        <Link href="/field-reports" className="block text-sm text-brand hover:underline">
          חזרה לרשימה
        </Link>
      </div>
    );
  }

  return (
    <div className="of-container mx-auto w-full max-w-5xl space-y-6 p-4 md:space-y-7 md:p-6 lg:space-y-8 lg:p-8">
      <header className="space-y-3">
        <Link
          href="/field-reports"
          className="text-sm text-brand hover:underline"
        >
          ← הדוחות שלי
        </Link>
        <h1 className="of-page-title text-2xl">
          {report.project_name || "דוח ביקור"}
        </h1>
        <p className="text-sm text-zinc-600">
          {report.visit_type_label_he} · תאריך ביקור: {report.visit_date}
        </p>
        <p className="text-xs text-zinc-500">
          {fieldReportDataSourceModeLabelHe(dataSourceMode)}
          {pinging ? " · בודק חיבור..." : ""}
        </p>
        <p className="text-sm">
          <span className="rounded-full bg-zinc-100 px-3 py-1 font-medium text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200">
            {visitReportPipelineStatusLabel(report)}
          </span>
        </p>
        {deleteEligible ? (
          <div className="pt-1">
            <Button
              variant="danger"
              size="sm"
              onClick={() => setDeleteDialogOpen(true)}
              disabled={deleteLoading || cancelLoading || finishLoading}
            >
              מחק דוח
            </Button>
          </div>
        ) : null}
        {report.is_editable && !editSession.blockingSession ? (
          <div>
            <VisitReportPrimaryActions
              report={report}
              isOnline={isOnline}
              canCloseOffline={canCloseOffline}
              isReopenedForEdit={isReopenedForEdit}
              reopenLoading={reopenLoading}
              onOpenFinishDialog={() => void openFinishDialog()}
              onCancelReport={() => setCancelDialogOpen(true)}
              cancelDisabled={cancelLoading || finishLoading}
              onConfirmReopenReport={() => void confirmReopenReport()}
            />
            <VisitReportPdfActions
              report={report}
              isReopenedForEdit={isReopenedForEdit}
              hasLocalPdf={hasLocalPdf}
              canFinalize={canFinalizeReport}
              isOnline={isOnline}
              className="max-lg:hidden"
              onCacheChange={setHasLocalPdf}
              onSetNotice={setPdfNotice}
              onSetError={setPdfError}
              onFinalizeStart={handleFinalizeStart}
              onFinalizeComplete={handleFinalizeComplete}
            />
          </div>
        ) : null}
        {!report.is_editable && report.can_reopen ? (
          <VisitReportPrimaryActions
            report={report}
            isOnline={isOnline}
            canCloseOffline={canCloseOffline}
            isReopenedForEdit={isReopenedForEdit}
            reopenLoading={reopenLoading}
            onOpenFinishDialog={() => void openFinishDialog()}
            onConfirmReopenReport={() => void confirmReopenReport()}
          />
        ) : null}
        <VisitReportPdfActions
          report={report}
          isReopenedForEdit={isReopenedForEdit}
          hasLocalPdf={hasLocalPdf}
          canFinalize={canFinalizeReport}
          isOnline={isOnline}
          className="max-lg:hidden"
          onCacheChange={setHasLocalPdf}
          onSetNotice={setPdfNotice}
          onSetError={setPdfError}
          onFinalizeStart={handleFinalizeStart}
          onFinalizeComplete={handleFinalizeComplete}
        />
        <VisitReportAlerts
          pdfNotice={pdfNotice}
          pdfError={pdfError}
          reopenError={reopenError}
          cancelError={cancelError}
        />
      </header>

      <FinishReportDialog
        open={finishOpen}
        loading={finishLoading}
        preview={closePreview}
        error={finishError}
        onCancel={() => {
          if (!finishLoading) {
            setFinishOpen(false);
            setFinishError("");
          }
        }}
        onConfirm={() => void confirmFinishReport()}
      />

      <CancelReportCreationDialog
        open={cancelDialogOpen}
        title="ביטול דוח"
        confirming={cancelLoading}
        onStay={() => {
          if (!cancelLoading) {
            setCancelDialogOpen(false);
            setCancelError("");
          }
        }}
        onConfirmCancel={() => void confirmCancelReport()}
      />

      <DeleteReportDialog
        open={deleteDialogOpen}
        reportTitle={report.project_name || report.visit_type_label_he || "דוח ביקור"}
        deleting={deleteLoading}
        onCancel={() => {
          if (!deleteLoading) {
            setDeleteDialogOpen(false);
            setDeleteError("");
          }
        }}
        onConfirm={() => void confirmDeleteReport()}
      />

      {deleteError ? (
        <p className="text-sm text-red-600">{deleteError}</p>
      ) : null}

      {editSession.blockingSession ? (
        <div className="space-y-3 rounded-xl border border-amber-300 bg-amber-50 px-4 py-4 text-sm text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100 md:px-5 md:py-5">
          <p>
            דוח אחר נפתח לעריכה במכשיר זה. ניתן לערוך דוח אחד בכל רגע.
          </p>
          <div className="flex flex-wrap gap-2.5">
            <Link
              href={fieldReportDetailPath(
                editSession.blockingSession.reportId
              )}
              className="of-focus-ring inline-flex min-h-12 items-center justify-center rounded-2xl border border-amber-400 px-5 py-2.5 text-sm font-semibold hover:bg-amber-100 dark:hover:bg-amber-900/40"
            >
              חזור לדוח הפעיל
            </Link>
            <Button
              variant="secondary"
              size="lg"
              className="min-h-12"
              onClick={() => editSession.claim()}
            >
              ערוך דוח זה במקום
            </Button>
          </div>
        </div>
      ) : null}

      {!editSession.blockingSession
      && shouldShowVisitIssueDiff(report)
      && report.project_id
      && serverVisitReportId(report) ? (
        <VisitReportIssueDiffPanel
          projectId={report.project_id}
          reportId={serverVisitReportId(report)!}
          isOnline={isOnline}
        />
      ) : null}

      {!editSession.blockingSession ? (
        <VisitReportEditor
          key={`${report.id}:${report.visit_type}`}
          report={report}
          hasLocalRecord={hasLocalRecord}
          onReportChange={setReport}
        />
      ) : null}

      {!editSession.blockingSession && report.is_editable ? (
        <section className="rounded-xl border border-zinc-200 bg-white/80 p-4 dark:border-zinc-800 dark:bg-zinc-900/40">
          <VisitReportPrimaryActions
            report={report}
            isOnline={isOnline}
            canCloseOffline={canCloseOffline}
            isReopenedForEdit={isReopenedForEdit}
            reopenLoading={reopenLoading}
            compact
            onOpenFinishDialog={() => void openFinishDialog()}
            onCancelReport={() => setCancelDialogOpen(true)}
            cancelDisabled={cancelLoading || finishLoading}
            onConfirmReopenReport={() => void confirmReopenReport()}
          />
        </section>
      ) : null}

      {!editSession.blockingSession && !report.is_editable && report.can_reopen ? (
        <section className="rounded-xl border border-zinc-200 bg-white/80 p-4 dark:border-zinc-800 dark:bg-zinc-900/40">
          <VisitReportPrimaryActions
            report={report}
            isOnline={isOnline}
            canCloseOffline={canCloseOffline}
            isReopenedForEdit={isReopenedForEdit}
            reopenLoading={reopenLoading}
            compact
            onOpenFinishDialog={() => void openFinishDialog()}
            onConfirmReopenReport={() => void confirmReopenReport()}
          />
        </section>
      ) : null}

      {!editSession.blockingSession
      && shouldShowVisitReportPdfActions(report, isReopenedForEdit) ? (
        <section className="rounded-xl border border-zinc-200 bg-white/80 p-4 dark:border-zinc-800 dark:bg-zinc-900/40 lg:hidden">
          <h2 className="mb-3 text-sm font-semibold text-zinc-700 dark:text-zinc-300">
            PDF
          </h2>
          <VisitReportPdfActions
            report={report}
            isReopenedForEdit={isReopenedForEdit}
            hasLocalPdf={hasLocalPdf}
            canFinalize={canFinalizeReport}
            isOnline={isOnline}
            stacked
            onCacheChange={setHasLocalPdf}
            onSetNotice={setPdfNotice}
            onSetError={setPdfError}
            onFinalizeStart={handleFinalizeStart}
            onFinalizeComplete={handleFinalizeComplete}
          />
        </section>
      ) : null}
    </div>
  );
}
