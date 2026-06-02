"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import {
  startTransition,
  useCallback,
  useEffect,
  useState,
} from "react";

import FinishReportDialog, {
  type ClosePreview,
} from "@/components/field-reports/FinishReportDialog";
import VisitReportAlerts from "@/components/field-reports/VisitReportAlerts";
import SendToCoreDialog from "@/components/field-reports/SendToCoreDialog";
import VisitReportPdfActions from "@/components/field-reports/VisitReportPdfActions";
import VisitReportPrimaryActions from "@/components/field-reports/VisitReportPrimaryActions";
import VisitReportEditor from "@/components/field-reports/VisitReportEditor";
import Button from "@/components/ui/Button";
import { useAuth } from "@/contexts/AuthContext";
import { useFieldReportEditSession } from "@/hooks/useFieldReportEditSession";
import { useFieldReportModule } from "@/hooks/useFieldReportModule";
import { apiFetch } from "@/lib/api/client";
import { buildClosePreview } from "@/lib/field-reports/close-preview";
import { processPendingSendRequest } from "@/lib/field-reports/process-send-queue";
import { downloadVisitReportPdf } from "@/lib/field-reports/pdf/generate-visit-report-pdf";
import {
  hasVisitReportPdfLocally,
} from "@/lib/field-reports/pdf/visit-report-pdf-store";
import type { OrganizationProfileSnapshot } from "@/lib/field-reports/pdf/types";
import {
  enqueuePendingSendRequest,
  loadPendingSendRequests,
  pendingSendPhaseLabelHe,
  removePendingSendRequest,
} from "@/lib/field-reports/send-queue";
import { useOffline } from "@/providers/OfflineProvider";

type VisitReportLine = {
  id: string;
  sort_order: number;
  description?: string | null;
  catalog_warning?: string | null;
  location?: string | null;
  trade?: string | null;
  status?: string | null;
  notes?: string | null;
  severity?: string | null;
  standard_ref?: string | null;
  issue_id?: string | null;
  has_photo?: boolean;
  photo_url?: string | null;
};

type VisitReport = {
  id: string;
  project_name?: string;
  visit_type: string;
  visit_type_label_he: string;
  status_label_he: string;
  visit_date: string;
  status: string;
  header_fields: Record<string, unknown>;
  catalog_version?: string | null;
  closed_at?: string | null;
  organization_profile_snapshot?: OrganizationProfileSnapshot | null;
  lines: VisitReportLine[];
  line_count?: number;
  is_editable: boolean;
  can_reopen?: boolean;
  can_send_to_core?: boolean;
  was_closed?: boolean;
};

export default function FieldVisitReportPage() {
  const params = useParams();
  const reportId = typeof params.id === "string" ? params.id : "";
  const { status: moduleStatus } = useFieldReportModule();
  const organizationId = moduleStatus?.organization_id || "";
  const { isOnline } = useOffline();
  const { profile } = useAuth();
  const editSession = useFieldReportEditSession(
    organizationId,
    reportId
  );
  const [report, setReport] = useState<VisitReport | null>(null);
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
  const pendingSendEntry =
    organizationId && reportId
      ? loadPendingSendRequests(organizationId).find(
          (entry) => entry.reportId === reportId
        )
      : null;
  const localPendingSend = Boolean(pendingSendEntry);
  const pendingSendPhase = pendingSendEntry?.syncPhase
    ? pendingSendPhaseLabelHe(pendingSendEntry.syncPhase)
    : "";
  const pendingSendError = pendingSendEntry?.lastError || "";
  const isServerPendingSend = report?.status === "PENDING_UPLOAD";
  const hasPendingSendFailure = localPendingSend && Boolean(pendingSendError);
  const showPendingSendState =
    isServerPendingSend || (localPendingSend && !hasPendingSendFailure);

  const isReopenedForEdit =
    report?.is_editable && Boolean(report?.was_closed);

  const loadReport = useCallback(async () => {
    if (!reportId) {
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await apiFetch(
        `/field-reports/visits/${reportId}`
      );

      if (!response.ok) {
        throw new Error("טעינת הדוח נכשלה");
      }

      setReport(await response.json());
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "טעינת הדוח נכשלה"
      );
    } finally {
      setLoading(false);
    }
  }, [reportId]);

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
    if (!reportId) {
      return;
    }

    let active = true;

    void hasVisitReportPdfLocally(reportId).then((exists) => {
      if (active) {
        setHasLocalPdf(exists);
      }
    });

    return () => {
      active = false;
    };
  }, [reportId, report?.status]);

  async function openFinishDialog() {
    if (!report?.is_editable) {
      return;
    }

    setFinishOpen(true);
    setFinishError("");
    setFinishLoading(true);

    const localPreview = buildClosePreview(report.lines);
    setClosePreview(localPreview);

    if (!isOnline) {
      setFinishLoading(false);
      return;
    }

    try {
      const response = await apiFetch(
        `/field-reports/visits/${report.id}/close-preview`
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

    if (!isOnline) {
      setFinishError("סגירת דוח דורשת חיבור לרשת");
      return;
    }

    try {
      setFinishLoading(true);
      setFinishError("");

      const response = await apiFetch(
        `/field-reports/visits/${report.id}/close`,
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
            : "הדוח נסגר אך הפקת PDF נכשלה — נסה שוב מהכפתור למטה."
        );
      }
    } catch (err: unknown) {
      setFinishError(
        err instanceof Error ? err.message : "סגירת הדוח נכשלה"
      );
    } finally {
      setFinishLoading(false);
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

      const response = await apiFetch(
        `/field-reports/visits/${report.id}/reopen`,
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
      const pendingRequest = enqueuePendingSendRequest(
        organizationId,
        report.id
      );

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
        const response = await apiFetch(
          `/field-reports/visits/${report.id}`
        );
        if (response.ok) {
          setReport(await response.json());
        }
      } catch {
        // If refresh fails, keep current UI state. The pending-send header is still correct via localStorage.
      }

      if (result.success) {
        setSendOpen(false);
        setSendError("");
        setSendNotice("הדוח נשלח לליבה וננעל בהצלחה.");
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

  function cancelPendingSend() {
    if (!organizationId || !report) {
      return;
    }

    removePendingSendRequest(organizationId, report.id);
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
        <p className="text-sm">
          <span className="rounded-full bg-zinc-100 px-3 py-1 font-medium text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200">
            {showPendingSendState
              ? "ממתין לשליחה"
              : report.status_label_he}
          </span>
        </p>
        {report.is_editable && !editSession.blockingSession ? (
          <div>
            <VisitReportPrimaryActions
              report={report}
              isOnline={isOnline}
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
              isReopenedForEdit={isReopenedForEdit}
              reopenLoading={reopenLoading}
              hasLocalPdf={hasLocalPdf}
              onOpenFinishDialog={() => void openFinishDialog()}
              onConfirmReopenReport={() => void confirmReopenReport()}
              onOpenSendDialog={openSendDialog}
            />
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
              href={`/field-reports/${editSession.blockingSession.reportId}`}
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

      {!editSession.blockingSession ? (
        <VisitReportEditor
          key={`${report.id}:${report.visit_type}`}
          report={report}
          onReportChange={setReport}
        />
      ) : null}

      {!editSession.blockingSession && report.is_editable ? (
        <section className="rounded-xl border border-zinc-200 bg-white/80 p-4 dark:border-zinc-800 dark:bg-zinc-900/40">
          <VisitReportPrimaryActions
            report={report}
            isOnline={isOnline}
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
