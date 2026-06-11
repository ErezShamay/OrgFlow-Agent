"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import FindingSimilarIssuesHint from "@/components/quality-issues/FindingSimilarIssuesHint";
import Button from "@/components/ui/Button";
import LinePhotoCapture, {
  type LinePhotosChangePayload,
} from "@/components/field-reports/LinePhotoCapture";
import LineGroupSelector from "@/components/field-reports/LineGroupSelector";
import { useDebouncedCallback } from "@/hooks/useDebouncedCallback";
import { useLockBackgroundScrollWhileOverlay } from "@/hooks/useLockBodyScroll";
import { FIELD_REPORT_LOCAL_AUTOSAVE_MS } from "@/lib/field-reports/local-autosave";
import {
  lineGroupFieldsFromSelection,
  selectionFromLineGroupFields,
} from "@/lib/field-reports/line-grouping";
import { catalogSeverityLabelHe } from "@/lib/field-reports/catalog-labels";
import {
  FR_TOUCH_BUTTON,
  FR_TOUCH_INPUT,
  FR_TOUCH_NOTES,
  FR_TOUCH_TEXTAREA,
} from "@/lib/field-reports/touch-input-class";

export type EditableReportLine = {
  id: string;
  location?: string | null;
  trade?: string | null;
  status?: string | null;
  description?: string | null;
  notes?: string | null;
  severity?: string | null;
  standard_ref?: string | null;
  issue_id?: string | null;
  has_catalog_issue?: boolean;
  has_photo?: boolean;
  photo_url?: string | null;
  photo_ids?: string[];
  photos?: Array<{ id: string; url: string }>;
  catalog_warning?: string | null;
  group_key?: string | null;
  group_label_he?: string | null;
  block_id?: string | null;
  linked_issue_id?: string | null;
};

const LINE_STATUS_OPTIONS = [
  { value: "", label: "-" },
  { value: "IN_PROGRESS", label: "בתהליך" },
  { value: "DONE", label: "בוצע" },
  { value: "NEEDS_ACTION", label: "יש להשלים" },
];

export type LineSaveOptions = {
  /** auto-save - ללא חסימת UI מלאה */
  silent?: boolean;
};

type ReportLineEditorProps = {
  reportId: string;
  projectId?: string | null;
  organizationId?: string | null;
  line: EditableReportLine;
  editable: boolean;
  saving: boolean;
  linking?: boolean;
  autosave?: boolean;
  autosaveDelayMs?: number;
  onSave: (
    lineId: string,
    payload: Record<string, unknown>,
    options?: LineSaveOptions
  ) => Promise<void>;
  onLinkRow?: (
    lineId: string,
    linkedIssueId: string | null
  ) => void | Promise<void>;
  onConvertToFreeText: (lineId: string) => Promise<void>;
  onDelete: (lineId: string) => Promise<void>;
  onPhotosChange: (lineId: string, payload: LinePhotosChangePayload) => void;
};

export default function ReportLineEditor({
  reportId,
  projectId = null,
  organizationId = null,
  line,
  editable,
  saving,
  linking = false,
  autosave = false,
  autosaveDelayMs = FIELD_REPORT_LOCAL_AUTOSAVE_MS,
  onSave,
  onLinkRow,
  onConvertToFreeText,
  onDelete,
  onPhotosChange,
}: ReportLineEditorProps) {
  const [expanded, setExpanded] = useState(false);
  const [draft, setDraft] = useState(() => lineToDraft(line));
  const draftSkipAutosave = useRef(true);

  useLockBackgroundScrollWhileOverlay(expanded);

  useEffect(() => {
    setDraft(lineToDraft(line));
    draftSkipAutosave.current = true;
  }, [line]);

  const debouncedAutosave = useDebouncedCallback(() => {
    if (!draft.description.trim()) {
      return;
    }

    void onSave(
      line.id,
      lineDraftToSavePayload(draft, line),
      { silent: true }
    );
  }, autosaveDelayMs);

  useEffect(() => {
    if (!expanded || !autosave || !editable) {
      return;
    }

    if (draftSkipAutosave.current) {
      draftSkipAutosave.current = false;
      return;
    }

    debouncedAutosave();
  }, [draft, expanded, autosave, editable, debouncedAutosave]);

  function closeEditor() {
    setDraft(lineToDraft(line));
    setExpanded(false);
  }

  function openEditor() {
    setDraft(lineToDraft(line));
    setExpanded(true);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!draft.description.trim()) {
      return;
    }

    await onSave(line.id, lineDraftToSavePayload(draft, line));
    setExpanded(false);
  }

  const photoCapture = (
    <LinePhotoCapture
      reportId={reportId}
      lineId={line.id}
      photos={line.photos}
      hasServerPhoto={Boolean(line.has_photo)}
      photoUrl={line.photo_url}
      disabled={!editable}
      onPhotosChange={(payload) => onPhotosChange(line.id, payload)}
    />
  );

  const editForm = (
    <form
      onSubmit={(event) => void handleSubmit(event)}
      className="space-y-3 md:space-y-4"
    >
      <LineGroupSelector
        value={draft.group}
        disabled={saving}
        onChange={(group) => setDraft((current) => ({ ...current, group }))}
      />
      <div className="grid gap-3 lg:grid-cols-2">
        <Field
          label="מיקום"
          value={draft.location}
          onChange={(value) =>
            setDraft((current) => ({ ...current, location: value }))
          }
        />
        <Field
          label="מלאכה"
          value={draft.trade}
          onChange={(value) =>
            setDraft((current) => ({ ...current, trade: value }))
          }
        />
        <label className="block space-y-1.5 text-sm">
          <span className="font-medium">סטטוס</span>
          <select
            className={FR_TOUCH_INPUT}
            value={draft.status}
            onChange={(event) =>
              setDraft((current) => ({
                ...current,
                status: event.target.value,
              }))
            }
          >
            {LINE_STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        {!line.has_catalog_issue ? (
          <Field
            label="חומרה"
            value={draft.severity}
            onChange={(value) =>
              setDraft((current) => ({
                ...current,
                severity: value,
              }))
            }
          />
        ) : null}
      </div>
      <label className="block space-y-1.5 text-sm">
        <span className="font-medium">תיאור *</span>
        <textarea
          className={FR_TOUCH_TEXTAREA}
          value={draft.description}
          onChange={(event) =>
            setDraft((current) => ({
              ...current,
              description: event.target.value,
            }))
          }
          required
        />
      </label>
      <label className="block space-y-1.5 text-sm">
        <span className="font-medium">הערות / פעולת תיקון</span>
        <textarea
          className={FR_TOUCH_NOTES}
          value={draft.notes}
          onChange={(event) =>
            setDraft((current) => ({
              ...current,
              notes: event.target.value,
            }))
          }
        />
      </label>
      <FindingSimilarIssuesHint
        projectId={projectId}
        organizationId={organizationId}
        reportId={reportId}
        lineId={line.id}
        disabled={!editable}
        linkedIssueId={line.linked_issue_id}
        linking={linking}
        location={draft.location}
        trade={draft.trade}
        group_key={line.group_key}
        issue_id={line.issue_id}
        onLinkIssue={
          onLinkRow
            ? (issueId) => onLinkRow(line.id, issueId)
            : undefined
        }
        onMarkNewIssue={
          onLinkRow ? () => onLinkRow(line.id, null) : undefined
        }
        onUnlinkIssue={
          onLinkRow ? () => onLinkRow(line.id, null) : undefined
        }
      />
      {line.has_catalog_issue ? (
        <Button
          variant="secondary"
          size="lg"
          className={FR_TOUCH_BUTTON}
          type="button"
          disabled={saving}
          onClick={() => void onConvertToFreeText(line.id)}
        >
          המר לתיאור חופשי (בלי ממצא במפרט)
        </Button>
      ) : null}
      <Button
        type="submit"
        size="lg"
        className={`w-full sm:w-auto ${FR_TOUCH_BUTTON}`}
        disabled={saving}
      >
        {saving ? "שומר..." : "שמור שורה"}
      </Button>
    </form>
  );

  const tabletSheet =
    expanded && typeof document !== "undefined"
      ? createPortal(
          <div
            className="fixed inset-0 z-[60] flex h-dvh max-h-dvh flex-col overscroll-none bg-zinc-50 dark:bg-zinc-950 lg:hidden"
            role="dialog"
            aria-modal="true"
            aria-label="עריכת שורת ממצא"
          >
            <header className="flex shrink-0 items-center justify-between gap-3 border-b border-zinc-200 bg-white px-4 py-3 pt-[max(0.75rem,env(safe-area-inset-top))] dark:border-zinc-800 dark:bg-zinc-900">
              <div className="min-w-0">
                <p className="text-xs text-zinc-500">עריכת שורה</p>
                <p className="truncate font-semibold">
                  {line.trade || "ללא מלאכה"}
                  {line.location ? ` · ${line.location}` : ""}
                </p>
              </div>
              <Button
                variant="secondary"
                size="lg"
                className={FR_TOUCH_BUTTON}
                type="button"
                disabled={saving}
                onClick={closeEditor}
              >
                סגור
              </Button>
            </header>
            <div className="min-h-0 flex-1 touch-pan-y overflow-y-auto overscroll-y-contain px-4 py-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
              {editForm}
              {photoCapture}
            </div>
          </div>,
          document.body
        )
      : null;

  return (
    <li className="rounded-xl border border-zinc-200 p-4 text-sm md:p-5">
      <div className="flex flex-wrap items-start justify-between gap-2.5">
        <button
          type="button"
          className="min-w-0 flex-1 text-right touch-manipulation disabled:cursor-default"
          disabled={!editable}
          onClick={() => {
            if (editable && !expanded) {
              openEditor();
            }
          }}
        >
          <p className="font-medium">
            {line.group_label_he ? (
              <span className="text-zinc-600">{line.group_label_he} · </span>
            ) : null}
            {line.trade || "ללא מלאכה"}
            {line.location ? ` · ${line.location}` : ""}
          </p>
          {line.issue_id ? (
            <p className="text-xs text-zinc-500">
              {line.issue_id}
              {line.standard_ref ? ` · תקן: ${line.standard_ref}` : ""}
              {line.severity
                ? ` · חומרה: ${catalogSeverityLabelHe(line.severity)}`
                : ""}
            </p>
          ) : (
            <p className="text-xs text-zinc-500">תיאור חופשי</p>
          )}
          {line.catalog_warning ? (
            <p className="mt-1 text-xs text-amber-800 dark:text-amber-300">
              {line.catalog_warning}
            </p>
          ) : null}
        </button>
        {editable ? (
          <div className="flex w-full flex-wrap gap-2 sm:w-auto">
            <Button
              variant="secondary"
              size="lg"
              className={`flex-1 sm:flex-none ${FR_TOUCH_BUTTON}`}
              type="button"
              disabled={saving}
              onClick={() => {
                if (expanded) {
                  closeEditor();
                } else {
                  openEditor();
                }
              }}
            >
              {expanded ? "סגור" : "ערוך"}
            </Button>
            <Button
              variant="secondary"
              size="lg"
              className={`flex-1 sm:flex-none ${FR_TOUCH_BUTTON}`}
              type="button"
              disabled={saving}
              onClick={() => void onDelete(line.id)}
            >
              מחק
            </Button>
          </div>
        ) : null}
      </div>

      {!expanded ? (
        <>
          <p className="mt-2 whitespace-pre-wrap">
            {line.description || "-"}
          </p>
          {line.notes ? (
            <p className="mt-1 text-zinc-600">הערות: {line.notes}</p>
          ) : null}
          {photoCapture}
        </>
      ) : (
        <div className="mt-3 hidden lg:block">
          {editForm}
          {photoCapture}
        </div>
      )}

      {tabletSheet}
    </li>
  );
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block space-y-1.5 text-sm">
      <span className="font-medium">{label}</span>
      <input
        className={FR_TOUCH_INPUT}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function lineToDraft(line: EditableReportLine) {
  return {
    location: line.location || "",
    trade: line.trade || "",
    status: line.status || "",
    description: line.description || "",
    notes: line.notes || "",
    severity: line.severity || "",
    group: selectionFromLineGroupFields(line),
  };
}

function lineDraftToSavePayload(
  draft: ReturnType<typeof lineToDraft>,
  line: EditableReportLine
): Record<string, unknown> {
  return {
    location: draft.location || null,
    trade: draft.trade || null,
    status: draft.status || null,
    description: draft.description,
    notes: draft.notes || null,
    severity: line.has_catalog_issue ? undefined : draft.severity || null,
    ...lineGroupFieldsFromSelection(draft.group),
  };
}
