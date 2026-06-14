"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import {
  startTransition,
  useCallback,
  useEffect,
  useState,
} from "react";

import FinishReportDialog, {
  type ClosePreview,
} from "@/components/field-reports/FinishReportDialog";
import PublishReportDialog from "@/components/field-reports/PublishReportDialog";
import VisitReportAlerts from "@/components/field-reports/VisitReportAlerts";
import SendToCoreDialog from "@/components/field-reports/SendToCoreDialog";
import VisitReportPdfActions from "@/components/field-reports/VisitReportPdfActions";
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
import { canPublishFieldReports } from "@/lib/field-reports/publish-access";
import {
  fetchPublishPreview,
  publishVisitReport,
  resolvePublishPdfBlob,
  type PublishPreview,
} from "@/lib/field-reports/publish-api";
import { processPendingSendRequest } from "@/lib/field-reports/process-send-queue";
import { downloadVisitReportPdf } from "@/lib/field-reports/pdf/generate-visit-report-pdf";
import {
  hasVisitReportPdfLocally,
} from "@/lib/field-reports/pdf/visit-report-pdf-store";
import type { OrganizationProfileSnapshot } from "@/lib/field-reports/pdf/types";
import {
  enqueuePendingSendRequest,
  loadPendingSendRequests,
  pendingSendMatchesReportKey,
  pendingSendPhaseLabelHe,
  removePendingSendRequest,
  type PendingSendRequest,
} from "@/lib/field-reports/send-queue";
import {
  fieldReportDetailPath,
  resolveFieldReportRouteId,
} from "@/lib/field-reports/routes";
import { shouldShowVisitIssueDiff } from "@/lib/quality-issues/visit-issue-diff";
import { useOffline } from "@/providers/OfflineProvider";

type VisitReport = VisitReportView & {
  organization_profile_snapshot?: OrganizationProfileSnapshot | null;
};

export default function FieldVisitReportPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const paramId = typeof params.id === "string" ? params.id : "";
  const reportId = resolveFieldReportRouteId(paramId, searchParams);
  const { status: moduleStatus } = useFieldReportModule();
  const organizationId = moduleStatus?.organization_id || "";
  const { isOnline } = useOffline();
  const { profile } = useAuth();
  const effectiveRole = useEffectiveRole();
  const canPublishReport = canPublishFieldReports(effectiveRole);
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
  const [sendOpen, setSendOpen] = useState(false);
  const [sendLoading, setSendLoading] = useState(false);
  const [sendError, setSendError] = useState("");
  const [sendNotice, setSendNotice] = useState("");
  const [pendingSendEntry, setPendingSendEntry] =
    useState<PendingSendRequest | null>(null);
  const [publishOpen, setPublishOpen] = useState(false);
  const [publishLoading, setPublishLoading] = useState(false);
  const [publishError, setPublishError] = useState("");
  const [publishNotice, setPublishNotice] = useState("");
  const [publishPreview, setPublishPreview] =
    useState<PublishPreview | null>(null);
  const localPendingSend = Boolean(pendingSendEntry);
  const pendingSendPhase = pendingSendEntry?.syncPhase
    ? pendingSendPhaseLabelHe(pendingSendEntry.syncPhase)
    : "";
  const pendingSendError = pendingSendEntry?.lastError || "";
  const isServerPendingSend = report?.status === "PENDING_UPLOAD";
  const hasPendingSendFailure = localPendingSend && Boolean(pendingSendError);
  const showPendingSendState =
    isServerPendingSend || (localPendingSend && !hasPendingSendFailure);

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

  useEffect(() => {
    if (!organizationId || !reportId) {
      setPendingSendEntry(null);
      return;
    }

    let cancelled = false;

    void loadPendingSendRequests(organizationId).then((entries) => {
      if (cancelled) {
        return;
      }

      setPendingSendEntry(
        entries.find((entry) =>
          pendingSendMatchesReportKey(entry, reportId)
        ) ?? null
      );
    });

    return () => {
      cancelled = true;
    };
  }, [organizationId, reportId]);

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
            // סגירה מקומית היא מקור האמת בשטח; סנכרון יושלם ב-FR-025.
          }
        }

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

  async function openPublishDialog() {
    if (!report?.can_publish || !canPublishReport) {
      return;
    }

    setPublishOpen(true);
    setPublishError("");
    setPublishLoading(true);

    try {
      const serverId = serverVisitReportId(report);
      if (!serverId) {
        throw new Error("פרסום דורש דוח שסונכרן לשרת");
      }

      setPublishPreview(await fetchPublishPreview(serverId));
    } catch (err: unknown) {
      setPublishError(
        err instanceof Error ? err.message : "טעינת תצוגה מקדימה נכשלה"
      );
    } finally {
      setPublishLoading(false);
    }
  }

  async function confirmPublishReport() {
    if (!report?.can_publish || !canPublishReport) {
      return;
    }

    if (!isOnline) {
      setPublishError("פרסום לפורטל דורש חיבור לרשת");
      return;
    }

    const serverId = serverVisitReportId(report);
    if (!serverId) {
      setPublishError("פרסום דורש דוח שסונכרן לשרת");
      return;
    }

    try {
      setPublishLoading(true);
      setPublishError("");

      const pdf = await resolvePublishPdfBlob(report, {
        full_name: profile?.full_name,
      });
      const published = await publishVisitReport(serverId, pdf);

      setReport({
        ...report,
        ...published,
        client_report_uuid: clientVisitReportUuid(report),
        server_report_id: serverId,
      });
      setPublishOpen(false);
      const pdfArchived = published.publish_result?.pdf_archived ?? false;
      const publishWarnings = published.publish_result?.warnings ?? [];
      if (pdfArchived) {
        setPublishNotice(
          `הדוח פורסם לפורטל. נוצרו ${published.publish_result?.issue_materialization.created_count ?? 0} ליקויים ברישום. ה-PDF נשמר בארכיון המסירות.`
        );
      } else {
        setPublishNotice(
          publishWarnings[0]
            || "הדוח פורסם אך ה-PDF לא נשמר בארכיון — יש להעלות PDF מחדש."
        );
      }
      setHasLocalPdf(true);
    } catch (err: unknown) {
      setPublishError(
        err instanceof Error ? err.message : "פרסום הדוח לפורטל נכשל"
      );
    } finally {
      setPublishLoading(false);
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

  function openSendDialog() {
    if (!report?.can_send_to_core) {
      return;
    }

    setSendOpen(true);
    setSendError("");
    setSendNotice("");
  }

  async function confirmSendToCore() {
    if (!report?.can_send_to_core || !organizationId) {
      return;
    }

    if (!hasLocalPdf) {
      setSendError("יש להפיק PDF במכשיר לפני שליחה לליבה");
      return;
    }

    try {
      setSendLoading(true);
      setSendError("");
      const sendReportId = serverVisitReportId(report) || report.id;
      const pendingRequest = await enqueuePendingSendRequest(
        organizationId,
        sendReportId
      );
      setPendingSendEntry(pendingRequest);

      if (!isOnline) {
        setSendOpen(false);
        setSendNotice(
          "הדוח סומן כממתין לשליחה. מטא־דאטה, תמונות ו-PDF יסונכרנו כשתחזור הרשת."
        );
        return;
      }

      const result = await processPendingSendRequest(pendingRequest);

      // Keep UI lock/editability consistent with server state.
      try {
        const refreshId = serverVisitReportId(report);
        if (refreshId) {
          const response = await apiFetch(
            `/field-reports/visits/${refreshId}`
          );
          if (response.ok) {
            setReport(await response.json());
          }
        }
      } catch {
        // If refresh fails, keep current UI state. The pending-send header is still correct via localStorage.
      }

      if (result.success) {
        setSendOpen(false);
        setSendError("");
        setSendNotice("הדוח נשלח לליבה וננעל בהצלחה.");
        window.dispatchEvent(
          new CustomEvent("field-report-sync-complete")
        );
      } else {
        setSendOpen(false);
        setSendError("");
        setSendNotice(
          "השליחה לא הושלמה. הדוח נשאר סגור וניתן לעריכה מחדש או לניסיון שליחה חוזר."
        );
      }
    } catch (err: unknown) {
      setSendError(
        err instanceof Error ? err.message : "שליחה לליבה נכשלה"
      );
      setSendNotice(
        "השליחה לא הושלמה. הדוח נשאר סגור וניתן לעריכה מחדש או לניסיון שליחה חוזר."
      );
    } finally {
      setSendLoading(false);
    }
  }

  async function cancelPendingSend() {
    if (!organizationId || !report) {
      return;
    }

    await removePendingSendRequest(
      organizationId,
      serverVisitReportId(report) || report.id
    );
    setPendingSendEntry(null);
    setSendError("");
    setSendNotice("ההמתנה לשליחה בוטלה. הדוח חזר למצב סגור וניתן לעריכה מחדש.");
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
        {publishNotice ? (
          <p className="text-sm text-emerald-700 dark:text-emerald-300">
            {publishNotice}
          </p>
        ) : null}
        {publishError && !publishOpen ? (
          <p className="text-sm text-red-600">{publishError}</p>
        ) : null}
        <p className="text-sm">
          <span className="rounded-full bg-zinc-100 px-3 py-1 font-medium text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200">
            {showPendingSendState
              ? "ממתין לשליחה"
              : report.is_published
                ? "פורסם לפורטל"
                : report.pending_publish
                  ? "ממתין לפרסום"
                  : report.status_label_he}
          </span>
        </p>
        {report.is_editable && !editSession.blockingSession ? (
          <div>
            <VisitReportPrimaryActions
              report={report}
              isOnline={isOnline}
              canCloseOffline={canCloseOffline}
              isReopenedForEdit={isReopenedForEdit}
              reopenLoading={reopenLoading}
              hasLocalPdf={hasLocalPdf}
              onOpenFinishDialog={() => void openFinishDialog()}
              onConfirmReopenReport={() => void confirmReopenReport()}
              onOpenSendDialog={openSendDialog}
            />
            <VisitReportPdfActions
              report={report}
              isReopenedForEdit={isReopenedForEdit}
              showPendingSendState={showPendingSendState}
              hasLocalPdf={hasLocalPdf}
              onCacheChange={setHasLocalPdf}
              onSetNotice={setPdfNotice}
              onSetError={setPdfError}
            />
          </div>
        ) : null}
        {!report.is_editable && report.can_reopen ? (
          <div>
            <VisitReportPrimaryActions
              report={report}
              isOnline={isOnline}
              canCloseOffline={canCloseOffline}
              isReopenedForEdit={isReopenedForEdit}
              reopenLoading={reopenLoading}
              hasLocalPdf={hasLocalPdf}
              onOpenFinishDialog={() => void openFinishDialog()}
              onConfirmReopenReport={() => void confirmReopenReport()}
              onOpenSendDialog={openSendDialog}
            />
            {canPublishReport && report.can_publish ? (
              <div className="pt-2">
                <Button
                  size="lg"
                  className="min-h-12"
                  onClick={() => void openPublishDialog()}
                  disabled={!isOnline || publishLoading}
                >
                  אשר ופרסם לפורטל
                </Button>
              </div>
            ) : null}
            {report.is_published ? (
              <p className="pt-2 text-sm text-emerald-700 dark:text-emerald-300">
                פורסם לפורטל הרוכש
              </p>
            ) : null}
          </div>
        ) : null}
        <VisitReportPdfActions
          report={report}
          isReopenedForEdit={isReopenedForEdit}
          showPendingSendState={showPendingSendState}
          hasLocalPdf={hasLocalPdf}
          onCacheChange={setHasLocalPdf}
          onSetNotice={setPdfNotice}
          onSetError={setPdfError}
        />
        <VisitReportAlerts
          report={report}
          pdfNotice={pdfNotice}
          pdfError={pdfError}
          reopenError={reopenError}
          sendNotice={sendNotice}
          showPendingSendState={showPendingSendState}
          pendingSendPhase={pendingSendPhase}
          pendingSendError={pendingSendError}
          localPendingSend={localPendingSend}
          hasPendingSendFailure={hasPendingSendFailure}
          onCancelPendingSend={cancelPendingSend}
          onOpenSendDialog={openSendDialog}
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

      <PublishReportDialog
        open={publishOpen}
        loading={publishLoading}
        preview={publishPreview}
        error={publishError}
        onCancel={() => {
          if (!publishLoading) {
            setPublishOpen(false);
            setPublishError("");
          }
        }}
        onConfirm={() => void confirmPublishReport()}
      />

      <SendToCoreDialog
        open={sendOpen}
        loading={sendLoading}
        offline={!isOnline}
        hasLocalPdf={hasLocalPdf}
        error={sendError}
        onCancel={() => {
          if (!sendLoading) {
            setSendOpen(false);
            setSendError("");
          }
        }}
        onConfirm={() => void confirmSendToCore()}
      />

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
            hasLocalPdf={hasLocalPdf}
            compact
            onOpenFinishDialog={() => void openFinishDialog()}
            onConfirmReopenReport={() => void confirmReopenReport()}
            onOpenSendDialog={openSendDialog}
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
            hasLocalPdf={hasLocalPdf}
            compact
            onOpenFinishDialog={() => void openFinishDialog()}
            onConfirmReopenReport={() => void confirmReopenReport()}
            onOpenSendDialog={openSendDialog}
          />
        </section>
      ) : null}
    </div>
  );
}
