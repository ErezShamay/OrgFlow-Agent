"use client";

import { FormEvent, type RefObject } from "react";

import CatalogIssuePicker, {
  type CatalogCategory,
  type CatalogFamily,
  type CatalogIssue,
} from "@/components/field-reports/CatalogIssuePicker";
import LineGroupSelector from "@/components/field-reports/LineGroupSelector";
import type { LinePhotosChangePayload } from "@/components/field-reports/LinePhotoCapture";
import QuickFindingPhotoButton from "@/components/field-reports/QuickFindingPhotoButton";
import ReportLineEditor, {
  type LineSaveOptions,
} from "@/components/field-reports/ReportLineEditor";
import Button from "@/components/ui/Button";
import type { LineGroupSelection } from "@/lib/field-reports/line-grouping";
import {
  FR_TOUCH_BUTTON,
  FR_TOUCH_INPUT,
  FR_TOUCH_NOTES,
  FR_TOUCH_TEXTAREA,
} from "@/lib/field-reports/touch-input-class";

export type ReportFindingLine = {
  id: string;
  sort_order: number;
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
] as const;

export type NewFindingLineDraft = {
  location: string;
  trade: string;
  status: string;
  description: string;
  notes: string;
};

export type ReportFindingsLinesPanelProps = {
  lines: ReportFindingLine[];
  editable: boolean;
  lineSaving: boolean;
  linkingRowId: string | null;
  reportId: string;
  projectId?: string | null;
  organizationId: string;
  catalogOpen: boolean;
  catalogFamilies: CatalogFamily[];
  catalogCategories: CatalogCategory[];
  catalogIssues: CatalogIssue[];
  catalogLoading: boolean;
  catalogError: string;
  catalogPickerRef: RefObject<HTMLDivElement | null>;
  pendingLineGroup: LineGroupSelection;
  newLine: NewFindingLineDraft;
  onLoadCatalog: () => void;
  onCloseCatalog: () => void;
  onConfirmCatalog: (issue: CatalogIssue) => void;
  onPhotoCaptured: (file: File) => void;
  onPendingLineGroupChange: (value: LineGroupSelection) => void;
  onNewLineChange: (patch: Partial<NewFindingLineDraft>) => void;
  onAddFreeLine: (event: FormEvent) => void;
  onSaveLine: (
    lineId: string,
    payload: Record<string, unknown>,
    options?: LineSaveOptions
  ) => Promise<void>;
  onLinkRow: (lineId: string, linkedIssueId: string | null) => void | Promise<void>;
  onConvertToFreeText: (lineId: string) => Promise<void>;
  onDeleteLine: (lineId: string) => Promise<void>;
  onPhotosChange: (lineId: string, patch: LinePhotosChangePayload) => void;
  lineAutosave?: boolean;
};

export default function ReportFindingsLinesPanel({
  lines,
  editable,
  lineSaving,
  linkingRowId,
  reportId,
  projectId = null,
  organizationId,
  catalogOpen,
  catalogFamilies,
  catalogCategories,
  catalogIssues,
  catalogLoading,
  catalogError,
  catalogPickerRef,
  pendingLineGroup,
  newLine,
  onLoadCatalog,
  onCloseCatalog,
  onConfirmCatalog,
  onPhotoCaptured,
  onPendingLineGroupChange,
  onNewLineChange,
  onAddFreeLine,
  onSaveLine,
  onLinkRow,
  onConvertToFreeText,
  onDeleteLine,
  onPhotosChange,
  lineAutosave = false,
}: ReportFindingsLinesPanelProps) {
  return (
    <div className="space-y-4" id="field-report-finding-lines">
      <div className="space-y-3">
        <div className="space-y-2">
          <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            צילום וצירוף תמונות
          </p>
          <p className="text-sm text-zinc-500">
            לכל ממצא בנפרד — צלם, בחר מהמפרט או הוסף שורה חופשית.
          </p>
        </div>
        {editable ? (
          <div className="space-y-3">
            <QuickFindingPhotoButton
              reportId={reportId}
              disabled={!editable}
              busy={lineSaving}
              onPhotoCaptured={onPhotoCaptured}
            />
            <div className="space-y-2">
              <Button
                variant="secondary"
                size="lg"
                className={`w-full sm:w-auto ${FR_TOUCH_BUTTON}`}
                disabled={catalogLoading || lineSaving}
                onClick={() => void onLoadCatalog()}
              >
                {catalogLoading ? "טוען מפרט..." : "בחר ממצא מהמפרט"}
              </Button>
              {catalogError ? (
                <p className="text-sm text-red-600" role="alert">
                  {catalogError}
                </p>
              ) : null}
            </div>
          </div>
        ) : null}
      </div>

      {editable ? (
        <div className="rounded-xl border border-zinc-200 bg-zinc-50/80 p-4 dark:border-zinc-800 dark:bg-zinc-900/40">
          <p className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
            קיבוץ לשורות חדשות
          </p>
          <LineGroupSelector
            value={pendingLineGroup}
            disabled={lineSaving}
            onChange={onPendingLineGroupChange}
          />
        </div>
      ) : null}

      {catalogOpen ? (
        <div ref={catalogPickerRef} id="catalog-issue-picker">
          <CatalogIssuePicker
            families={catalogFamilies}
            categories={catalogCategories}
            issues={catalogIssues}
            disabled={lineSaving}
            onClose={onCloseCatalog}
            onConfirm={onConfirmCatalog}
          />
        </div>
      ) : null}

      {lines.length === 0 ? (
        <div className="rounded-xl border border-dashed border-amber-300 bg-amber-50/80 px-4 py-4 text-sm text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100">
          <p className="font-medium">אין ממצאים עדיין</p>
          <p className="mt-2 text-amber-900/90 dark:text-amber-200/90">
            השתמש ב«צלם ממצא» (2 לחיצות), בחר ממצא מהמפרט, או הוסף שורה חופשית
            למטה.
          </p>
        </div>
      ) : (
        <ul className="space-y-3">
          {lines.map((line) => (
            <ReportLineEditor
              key={line.id}
              reportId={reportId}
              projectId={projectId}
              organizationId={organizationId}
              line={line}
              editable={editable}
              saving={lineSaving}
              linking={linkingRowId === line.id}
              autosave={lineAutosave}
              onSave={onSaveLine}
              onLinkRow={onLinkRow}
              onConvertToFreeText={onConvertToFreeText}
              onDelete={onDeleteLine}
              onPhotosChange={onPhotosChange}
            />
          ))}
        </ul>
      )}

      {editable ? (
        <form
          onSubmit={(event) => void onAddFreeLine(event)}
          className="space-y-3 rounded-xl border border-dashed border-zinc-300 p-4 md:space-y-4 md:p-5"
        >
          <h3 className="font-medium">שורה חופשית</h3>
          <div className="grid gap-3 md:grid-cols-2">
            <label className="block space-y-1 text-sm">
              <span>מיקום</span>
              <input
                className={FR_TOUCH_INPUT}
                value={newLine.location}
                onChange={(event) =>
                  onNewLineChange({ location: event.target.value })
                }
              />
            </label>
            <label className="block space-y-1 text-sm">
              <span>מלאכה</span>
              <input
                className={FR_TOUCH_INPUT}
                value={newLine.trade}
                onChange={(event) =>
                  onNewLineChange({ trade: event.target.value })
                }
              />
            </label>
            <label className="block space-y-1 text-sm">
              <span>סטטוס</span>
              <select
                className={FR_TOUCH_INPUT}
                value={newLine.status}
                onChange={(event) =>
                  onNewLineChange({ status: event.target.value })
                }
              >
                {LINE_STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="block space-y-1 text-sm">
            <span>תיאור *</span>
            <textarea
              className={FR_TOUCH_TEXTAREA}
              value={newLine.description}
              onChange={(event) =>
                onNewLineChange({ description: event.target.value })
              }
              required
            />
          </label>
          <label className="block space-y-1 text-sm">
            <span>הערות / פעולת תיקון</span>
            <textarea
              className={FR_TOUCH_NOTES}
              value={newLine.notes}
              onChange={(event) =>
                onNewLineChange({ notes: event.target.value })
              }
            />
          </label>
          <Button
            type="submit"
            size="lg"
            className={`w-full sm:w-auto ${FR_TOUCH_BUTTON}`}
            disabled={lineSaving}
          >
            {lineSaving ? "שומר..." : "הוסף שורה חופשית"}
          </Button>
        </form>
      ) : null}
    </div>
  );
}
