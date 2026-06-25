"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import type {
  CatalogCategory,
  CatalogFamily,
  CatalogIssue,
} from "@/components/field-reports/CatalogIssuePicker";
import ReportBlocksManager from "@/components/field-reports/ReportBlocksManager";
import ReportFindingsLinesPanel from "@/components/field-reports/ReportFindingsLinesPanel";
import ReportFixedBlocksSection from "@/components/field-reports/ReportFixedBlocksSection";
import SupervisionChecklistEditor from "@/components/field-reports/SupervisionChecklistEditor";
import ReportProjectMetadataSection from "@/components/field-reports/ReportProjectMetadataSection";
import ReportStakeholdersSection from "@/components/field-reports/ReportStakeholdersSection";
import { type LineSaveOptions } from "@/components/field-reports/ReportLineEditor";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { useDebouncedCallback } from "@/hooks/useDebouncedCallback";
import { toast } from "sonner";
import { useFieldReportModule } from "@/hooks/useFieldReportModule";
import { useFieldReportNetworkStatus } from "@/hooks/useFieldReportNetworkStatus";
import { apiFetch } from "@/lib/api/client";
import { catalogFamilyLabelHe } from "@/lib/field-reports/catalog-labels";
import {
  loadOfflineCatalogForPicker,
  OFFLINE_CATALOG_UNAVAILABLE_MESSAGE,
} from "@/lib/field-reports/catalog-offline";
import {
  FIELD_REPORT_LOCAL_AUTOSAVE_MS,
  fieldReportHeaderAutosaveDelayMs,
} from "@/lib/field-reports/local-autosave";
import {
  normalizeHeaderFields,
  patchHeaderFieldsBlocks,
  patchHeaderFieldsStakeholders,
  serializeHeaderFieldsForApi,
} from "@/lib/field-reports/header-fields";
import { fetchProjectPrefill } from "@/lib/field-reports/new-report-form";
import {
  applyProjectPrefillToHeaderFields,
  headerNeedsProjectPrefill,
} from "@/lib/field-reports/project-header-prefill";
import { saveReportMetadataDraft } from "@/lib/field-reports/report-metadata-draft";
import {
  defaultLineGroupSelection,
  lineGroupFieldsFromSelection,
  type LineGroupSelection,
} from "@/lib/field-reports/line-grouping";
import {
  FR_TOUCH_BUTTON,
  FR_TOUCH_INPUT,
  FR_TOUCH_TEXTAREA,
} from "@/lib/field-reports/touch-input-class";
import { useFieldReportDataSource } from "@/hooks/useFieldReportDataSource";
import { createClientLineUuid, isClientUuid } from "@/lib/field-reports/ids";
import {
  deleteLinePhotoLocally,
  saveLinePhotoLocally,
} from "@/lib/field-reports/line-photo-store";
import { uploadLinePhotoForReport } from "@/lib/field-reports/line-photo-upload";
import { buildQuickFindingLinePayload } from "@/lib/field-reports/quick-finding-photo";
import {
  clientVisitReportUuid,
  localVisitReportToView,
  type VisitReportView,
} from "@/lib/field-reports/visit-report-view";
import { syncSupervisionDefectDraftsForReport } from "@/lib/field-reports/checklist-defect-draft";
import { isSupervisionChecklistReport } from "@/lib/field-reports/supervision-checklist-builder";
import { resolveInspectMode } from "@/lib/field-reports/quick-inspect";
import {
  UNSPECIFIED_FIELD_LABEL_HE,
  normalizeOptionalTextInput,
  optionalTextForSave,
} from "@/lib/validation/optional-field-display";
import {
  extractProjectDatesFromHeaderFields,
  validateProjectDates,
} from "@/lib/validation/project-dates";
import type { SupervisionChecklistBlock } from "@/lib/field-reports/schema/types";
import {
  deleteLine as deleteLocalLine,
  getLocalReport,
  saveLocalReport,
  upsertLine,
} from "@/lib/field-reports/repositories/reports-repository";

type ReportLine = {
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

type VisitReport = VisitReportView & {
  lines: ReportLine[];
};

type VisitReportEditorProps = {
  report: VisitReport;
  onReportChange: (report: VisitReport) => void;
  /** דוח נטען מ-IndexedDB - מכריח שמירת שורות/כותרת מקומית גם כשה-ping ל-API מצליח. */
  hasLocalRecord?: boolean;
};

export default function VisitReportEditor({
  report,
  onReportChange,
  hasLocalRecord = false,
}: VisitReportEditorProps) {
  const clientReportUuid = clientVisitReportUuid(report);
  const {
    useLocalReports,
    canCallVisitReportApi,
    mode: dataSourceMode,
  } = useFieldReportDataSource({
    hasLocalReport:
      hasLocalRecord
      || isClientUuid(clientReportUuid),
    serverReportId: report.server_report_id ?? null,
  });
  const { status: moduleStatus } = useFieldReportModule();
  const { canSync } = useFieldReportNetworkStatus();
  const organizationId = moduleStatus?.organization_id || "";
  const [saving, setSaving] = useState(false);
  const [saveState, setSaveState] = useState<
    "idle" | "saving" | "saved" | "offline"
  >("idle");
  const [lineSaving, setLineSaving] = useState(false);
  const [linkingRowId, setLinkingRowId] = useState<string | null>(null);
  const [lineAutosaveState, setLineAutosaveState] = useState<
    "idle" | "saving" | "saved"
  >("idle");
  const [error, setError] = useState("");
  const [headerFields, setHeaderFields] = useState(() =>
    normalizeHeaderFields(report.header_fields, report.visit_type, {
      lines: report.lines,
      visitDate: report.visit_date,
    })
  );
  const headerInitialized = useRef(false);
  const projectPrefillAttempted = useRef(false);
  const [catalogOpen, setCatalogOpen] = useState(false);
  const [catalogFamilies, setCatalogFamilies] = useState<CatalogFamily[]>(
    []
  );
  const [catalogCategories, setCatalogCategories] = useState<
    CatalogCategory[]
  >([]);
  const [catalogIssues, setCatalogIssues] = useState<CatalogIssue[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogError, setCatalogError] = useState("");
  const catalogPickerRef = useRef<HTMLDivElement | null>(null);

  const [newLine, setNewLine] = useState({
    location: "",
    trade: "",
    status: "",
    description: "",
    notes: "",
  });
  const [pendingLineGroup, setPendingLineGroup] = useState<LineGroupSelection>(
    defaultLineGroupSelection()
  );

  async function persistHeaderLocally() {
    const record = await getLocalReport(clientReportUuid);
    if (!record) {
      throw new Error("דוח מקומי לא נמצא");
    }

    const updated = await saveLocalReport({
      ...record,
      header_fields: serializeHeaderFieldsForApi(headerFields),
    });
    onReportChange(localVisitReportToView(updated) as VisitReport);
    setSaveState("saved");
  }

  async function saveHeaderFields() {
    if (!report.is_editable) {
      return;
    }

    const dateError = validateProjectDates(
      extractProjectDatesFromHeaderFields(
        headerFields as Record<string, unknown>
      )
    );
    if (dateError) {
      setError(dateError);
      setSaveState("idle");
      return;
    }

    try {
      setSaving(true);
      setError("");

      if (useLocalReports) {
        await persistHeaderLocally();
        return;
      }

      const serverId = report.server_report_id;
      if (!serverId) {
        throw new Error("אין מזהה שרת לדוח - שמירה מקומית בלבד");
      }

      const response = await apiFetch(
        `/field-reports/visits/${serverId}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            header_fields: serializeHeaderFieldsForApi(headerFields),
          }),
        }
      );

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(
          payload.error?.message
            || payload.message
            || "שמירת פרטי הדוח נכשלה"
        );
      }

      onReportChange(await response.json());
      setSaveState("saved");
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "שמירת פרטי הדוח נכשלה"
      );
      setSaveState("idle");
    } finally {
      setSaving(false);
    }
  }

  const headerAutosaveMs = fieldReportHeaderAutosaveDelayMs(useLocalReports);

  const debouncedSaveHeader = useDebouncedCallback(() => {
    if (!report.is_editable) {
      return;
    }

    const dateError = validateProjectDates(
      extractProjectDatesFromHeaderFields(
        headerFields as Record<string, unknown>
      )
    );
    if (dateError) {
      setError(dateError);
      setSaveState("idle");
      return;
    }

    if (useLocalReports) {
      setSaveState("saving");
      void persistHeaderLocally().catch((err: unknown) => {
        setError(
          err instanceof Error
            ? err.message
            : "שמירת פרטי הדוח במכשיר נכשלה"
        );
        setSaveState("idle");
      });
      return;
    }

    if (!canCallVisitReportApi) {
      if (organizationId) {
        saveReportMetadataDraft(
          organizationId,
          report.id,
          serializeHeaderFieldsForApi(headerFields)
        );
      }
      setSaveState("offline");
      return;
    }

    void saveHeaderFields();
  }, headerAutosaveMs);

  useEffect(() => {
    projectPrefillAttempted.current = false;
  }, [clientReportUuid]);

  useEffect(() => {
    if (
      !report.is_editable
      || !report.project_id
      || projectPrefillAttempted.current
    ) {
      return;
    }

    if (!headerNeedsProjectPrefill(headerFields)) {
      projectPrefillAttempted.current = true;
      return;
    }

    projectPrefillAttempted.current = true;

    void fetchProjectPrefill(report.project_id).then((prefill) => {
      if (!prefill) {
        return;
      }

      setHeaderFields((current) => {
        if (!headerNeedsProjectPrefill(current)) {
          return current;
        }

        return applyProjectPrefillToHeaderFields(current, prefill);
      });
    });
  }, [report.is_editable, report.project_id]);

  useEffect(() => {
    if (!report.is_editable) {
      return;
    }

    if (!headerInitialized.current) {
      headerInitialized.current = true;
      return;
    }

    setSaveState("saving");
    debouncedSaveHeader();
  }, [
    headerFields,
    report.is_editable,
    debouncedSaveHeader,
    canCallVisitReportApi,
    useLocalReports,
  ]);

  async function persistLinePhotosLocally(
    lineId: string,
    payload: {
      has_photo: boolean;
      photo_ids: string[];
    }
  ) {
    const updated = await upsertLine(clientReportUuid, {
      client_line_uuid: lineId,
      has_photo: payload.has_photo,
      photo_ids: payload.photo_ids,
    });

    if (updated) {
      onReportChange(localVisitReportToView(updated) as VisitReport);
      setLineAutosaveState("saved");
    }
  }

  const debouncedPersistLinePhotos = useDebouncedCallback(
    (lineId: string, payload: { has_photo: boolean; photo_ids: string[] }) => {
      setLineAutosaveState("saving");
      void persistLinePhotosLocally(lineId, payload).catch((err: unknown) => {
        setError(
          err instanceof Error
            ? err.message
            : "שמירת תמונות במכשיר נכשלה"
        );
        setLineAutosaveState("idle");
      });
    },
    FIELD_REPORT_LOCAL_AUTOSAVE_MS
  );

  function updateLinePhotosState(
    lineId: string,
    payload: {
      has_photo: boolean;
      photo_ids: string[];
      photos: Array<{ id: string; url: string }>;
      photo_url: string | null;
    }
  ) {
    onReportChange({
      ...report,
      lines: report.lines.map((line) =>
        line.id === lineId
          ? {
              ...line,
              has_photo: payload.has_photo,
              photo_ids: payload.photo_ids,
              photos: payload.photos,
              photo_url: payload.photo_url,
            }
          : line
      ),
    });

    if (useLocalReports) {
      debouncedPersistLinePhotos(lineId, {
        has_photo: payload.has_photo,
        photo_ids: payload.photo_ids,
      });
    }
  }

  function scrollCatalogPickerIntoView() {
    requestAnimationFrame(() => {
      catalogPickerRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    });
  }

  function openCatalogPicker() {
    setCatalogOpen(true);
    scrollCatalogPickerIntoView();
  }

  async function loadCatalog() {
    if (catalogIssues.length > 0) {
      setCatalogError("");
      openCatalogPicker();
      return;
    }

    try {
      setCatalogLoading(true);
      setCatalogError("");
      setError("");

      if (organizationId) {
        const offlineCatalog = await loadOfflineCatalogForPicker(
          organizationId,
          report.visit_type
        );

        if (offlineCatalog) {
          applyCatalogPayload(offlineCatalog);
          openCatalogPicker();
          return;
        }
      }

      if (!canCallVisitReportApi) {
        throw new Error(OFFLINE_CATALOG_UNAVAILABLE_MESSAGE);
      }

      const response = await apiFetch(
        `/field-reports/catalog?visit_type=${encodeURIComponent(report.visit_type)}`
      );

      if (!response.ok) {
        throw new Error("טעינת המפרט נכשלה");
      }

      const payload = await response.json();
      applyCatalogPayload(payload);

      if (!payload.issues?.length) {
        throw new Error("המפרט ריק - בצע «הכנה לא מקוון» מחדש כשיש רשת.");
      }

      openCatalogPicker();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "טעינת המפרט נכשלה";
      setCatalogError(message);
      setError(message);
      toast.error(message);
    } finally {
      setCatalogLoading(false);
    }
  }

  function applyCatalogPayload(payload: {
    families?: CatalogFamily[];
    categories?: CatalogCategory[];
    issues?: CatalogIssue[];
  }) {
    setCatalogFamilies(
      (payload.families || []).map((family) => ({
        ...family,
        label_he: catalogFamilyLabelHe(
          family.top_family,
          family.label_he
        ),
      }))
    );
    setCatalogCategories(payload.categories || []);
    setCatalogIssues(payload.issues || []);
  }

  const catalogLineWarnings = useMemo(
    () =>
      report.lines.filter((line) => Boolean(line.catalog_warning)).length,
    [report.lines]
  );

  const hasExplicitBlocks = useMemo(() => {
    const raw = report.header_fields?.blocks;
    return Array.isArray(raw) && raw.length > 0;
  }, [report.header_fields]);

  const isSupervisionReport = useMemo(
    () => isSupervisionChecklistReport(headerFields.blocks),
    [headerFields.blocks]
  );

  const supervisionChecklistBlock = useMemo(() => {
    const match = headerFields.blocks.find(
      (block): block is SupervisionChecklistBlock =>
        block.kind === "supervision_checklist"
    );
    return match ?? null;
  }, [headerFields.blocks]);

  const inspectMode = useMemo(
    () => resolveInspectMode(report.header_fields?.supervision_meta),
    [report.header_fields?.supervision_meta]
  );

  function updateSupervisionChecklistBlock(nextBlock: SupervisionChecklistBlock) {
    setHeaderFields((current) =>
      patchHeaderFieldsBlocks(
        current,
        current.blocks.map((block) =>
          block.id === nextBlock.id ? nextBlock : block
        ),
        report.visit_type
      )
    );

    void (async () => {
      const record = await getLocalReport(clientReportUuid);
      if (!record) {
        return;
      }

      const currentHeader = normalizeHeaderFields(
        record.header_fields,
        record.visit_type,
        {
          lines: record.lines,
          visitDate: record.visit_date,
        }
      );
      const patchedHeader = patchHeaderFieldsBlocks(
        currentHeader,
        currentHeader.blocks.map((block) =>
          block.id === nextBlock.id ? nextBlock : block
        ),
        record.visit_type
      );
      const patchedRecord = {
        ...record,
        header_fields: serializeHeaderFieldsForApi(patchedHeader),
      };

      try {
        const withDrafts = await syncSupervisionDefectDraftsForReport(
          patchedRecord
        );
        await saveLocalReport(withDrafts);
      } catch {
        // Draft sync is best-effort until report sync completes.
      }
    })();
  }

  async function shouldSaveLinesLocally(): Promise<boolean> {
    if (useLocalReports) {
      return true;
    }

    return Boolean(await getLocalReport(clientReportUuid));
  }

  async function addFreeLine(event: FormEvent) {
    event.preventDefault();

    if (!report.is_editable) {
      toast.warning("הדוח אינו בעריכה - לא ניתן להוסיף שורה");
      return;
    }

    if (!newLine.description.trim()) {
      const message = "יש למלא תיאור לשורה";
      setError(message);
      toast.error(message);
      return;
    }

    try {
      setLineSaving(true);
      setError("");

      if (await shouldSaveLinesLocally()) {
        const updated = await upsertLine(clientReportUuid, {
          location: newLine.location || null,
          trade: newLine.trade || null,
          status: newLine.status || null,
          description: newLine.description,
          notes: newLine.notes || null,
          ...lineGroupFieldsFromSelection(pendingLineGroup),
        });

        if (!updated) {
          throw new Error("הוספת שורה במכשיר נכשלה");
        }

        onReportChange(localVisitReportToView(updated) as VisitReport);
      } else {
        const serverId = report.server_report_id;
        if (!serverId) {
          throw new Error("אין מזהה שרת לדוח");
        }

        const response = await apiFetch(
          `/field-reports/visits/${serverId}/lines`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              location: newLine.location || null,
              trade: newLine.trade || null,
              status: newLine.status || null,
              description: newLine.description,
              notes: newLine.notes || null,
              ...lineGroupFieldsFromSelection(pendingLineGroup),
            }),
          }
        );

        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          throw new Error(
            payload.error?.message
              || payload.message
              || "הוספת שורה נכשלה"
          );
        }

        const createdLine = await response.json();
        onReportChange({
          ...report,
          lines: [...report.lines, createdLine],
          line_count: report.lines.length + 1,
        });
      }
      setNewLine({
        location: "",
        trade: "",
        status: "",
        description: "",
        notes: "",
      });
      setPendingLineGroup(defaultLineGroupSelection());
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "הוספת שורה נכשלה";
      setError(message);
      toast.error(message);
    } finally {
      setLineSaving(false);
    }
  }

  async function addCatalogLine(issue: CatalogIssue) {
    if (!report.is_editable) {
      toast.warning("הדוח אינו בעריכה - לא ניתן להוסיף שורה");
      return;
    }

    try {
      setLineSaving(true);
      setError("");

      if (await shouldSaveLinesLocally()) {
        const updated = await upsertLine(clientReportUuid, {
          issue_id: issue.issue_id,
          description: issue.issue_name_he,
          severity: issue.severity ?? null,
          standard_ref: issue.standard_ref ?? null,
          catalog_reference_id: issue.catalog_reference_id ?? null,
          ...lineGroupFieldsFromSelection(pendingLineGroup),
        });

        if (!updated) {
          throw new Error("הוספת ממצא במכשיר נכשלה");
        }

        onReportChange(localVisitReportToView(updated) as VisitReport);
      } else {
        const serverId = report.server_report_id;
        if (!serverId) {
          throw new Error("אין מזהה שרת לדוח");
        }

        const response = await apiFetch(
          `/field-reports/visits/${serverId}/lines`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              issue_id: issue.issue_id,
              ...lineGroupFieldsFromSelection(pendingLineGroup),
            }),
          }
        );

        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          throw new Error(
            payload.error?.message
              || payload.message
              || "הוספת ממצא מהמפרט נכשלה"
          );
        }

        const createdLine = await response.json();
        onReportChange({
          ...report,
          lines: [...report.lines, createdLine],
        });
      }

      setCatalogOpen(false);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "הוספת ממצא מהמפרט נכשלה"
      );
    } finally {
      setLineSaving(false);
    }
  }

  async function addQuickFindingFromPhoto(file: File) {
    if (!report.is_editable) {
      toast.warning("הדוח אינו בעריכה - לא ניתן להוסיף ממצא");
      return;
    }

    setLineSaving(true);
    setError("");

    try {
      const linePayload = buildQuickFindingLinePayload({
        group: pendingLineGroup,
        sequence: report.lines.length + 1,
      });
      const lineId = linePayload.client_line_uuid;
      let photoReportKey = report.server_report_id ?? clientReportUuid;
      let photoLineId = lineId;
      let hadPhotoBefore = false;

      if (await shouldSaveLinesLocally()) {
        const updated = await upsertLine(clientReportUuid, linePayload);

        if (!updated) {
          throw new Error("יצירת שורת ממצא במכשיר נכשלה");
        }

        const view = localVisitReportToView(updated) as VisitReport;
        const createdLine =
          view.lines.find((line) => line.id === lineId)
          ?? view.lines[view.lines.length - 1];

        if (!createdLine) {
          throw new Error("יצירת שורת ממצא במכשיר נכשלה");
        }

        photoLineId = createdLine.id;
        photoReportKey = clientReportUuid;
        hadPhotoBefore = Boolean(createdLine.has_photo);
        onReportChange(view);
      } else {
        const serverId = report.server_report_id;
        if (!serverId) {
          throw new Error("אין מזהה שרת לדוח");
        }

        const response = await apiFetch(
          `/field-reports/visits/${serverId}/lines`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              location: linePayload.location ?? null,
              description: linePayload.description,
              group_key: linePayload.group_key ?? null,
              group_label_he: linePayload.group_label_he ?? null,
            }),
          }
        );

        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          throw new Error(
            payload.error?.message
              || payload.message
              || "יצירת שורת ממצא נכשלה"
          );
        }

        const createdLine = await response.json();
        photoLineId = String(createdLine.id);
        photoReportKey = serverId;
        hadPhotoBefore = Boolean(createdLine.has_photo);
        onReportChange({
          ...report,
          lines: [...report.lines, createdLine],
          line_count: report.lines.length + 1,
        });
      }

      const localPhotoId = await saveLinePhotoLocally(
        photoReportKey,
        photoLineId,
        file,
        { pendingUpload: !canSync }
      );

      if (canSync) {
        try {
          const uploadedLine = await uploadLinePhotoForReport(
            photoReportKey,
            photoLineId,
            file,
            {
              photoId: localPhotoId,
              useLegacySinglePhotoEndpoint: !hadPhotoBefore,
            }
          );
          await deleteLinePhotoLocally(
            photoReportKey,
            photoLineId,
            localPhotoId
          );

          const photoIds = Array.isArray(uploadedLine.photo_ids)
            ? uploadedLine.photo_ids.map(String)
            : [localPhotoId];
          const photos = Array.isArray(uploadedLine.photos)
            ? uploadedLine.photos.map((photo) => ({
                id: String((photo as { id: string }).id),
                url: String((photo as { url: string }).url),
              }))
            : [];

          updateLinePhotosState(photoLineId, {
            has_photo: Boolean(uploadedLine.has_photo),
            photo_ids: photoIds,
            photos,
            photo_url:
              typeof uploadedLine.photo_url === "string"
                ? uploadedLine.photo_url
                : null,
          });
        } catch (uploadError: unknown) {
          await saveLinePhotoLocally(photoReportKey, photoLineId, file, {
            pendingUpload: true,
            photoId: localPhotoId,
          });
          updateLinePhotosState(photoLineId, {
            has_photo: true,
            photo_ids: [localPhotoId],
            photos: [],
            photo_url: null,
          });
          if (await shouldSaveLinesLocally()) {
            await persistLinePhotosLocally(photoLineId, {
              has_photo: true,
              photo_ids: [localPhotoId],
            });
          }
          throw uploadError;
        }
      } else {
        updateLinePhotosState(photoLineId, {
          has_photo: true,
          photo_ids: [localPhotoId],
          photos: [],
          photo_url: null,
        });

        if (await shouldSaveLinesLocally()) {
          await persistLinePhotosLocally(photoLineId, {
            has_photo: true,
            photo_ids: [localPhotoId],
          });
        }
      }

      toast.success("נוספה שורת ממצא עם תמונה");
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "יצירת שורת ממצא מתמונה נכשלה";
      setError(message);
      toast.error(message);
    } finally {
      setLineSaving(false);
    }
  }

  async function saveLine(
    lineId: string,
    payload: Record<string, unknown>,
    options?: LineSaveOptions
  ) {
    if (!report.is_editable) {
      return;
    }

    const silent = Boolean(options?.silent);

    try {
      if (!silent) {
        setLineSaving(true);
      } else {
        setLineAutosaveState("saving");
      }
      setError("");

      if (await shouldSaveLinesLocally()) {
        const updated = await upsertLine(clientReportUuid, {
          client_line_uuid: lineId,
          ...payload,
        });

        if (!updated) {
          throw new Error("עדכון שורה במכשיר נכשל");
        }

        onReportChange(localVisitReportToView(updated) as VisitReport);
        if (silent) {
          setLineAutosaveState("saved");
        }
      } else {
        const serverId = report.server_report_id;
        if (!serverId) {
          throw new Error("אין מזהה שרת לדוח");
        }

        const response = await apiFetch(
          `/field-reports/visits/${serverId}/lines/${lineId}`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          }
        );

        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(
            body.error?.message || body.message || "עדכון שורה נכשל"
          );
        }

        const updatedLine = await response.json();
        onReportChange({
          ...report,
          lines: report.lines.map((line) =>
            line.id === lineId ? { ...line, ...updatedLine } : line
          ),
        });
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "עדכון שורה נכשל");
      if (silent) {
        setLineAutosaveState("idle");
      }
    } finally {
      if (!silent) {
        setLineSaving(false);
      }
    }
  }

  async function linkFindingRow(
    lineId: string,
    linkedIssueId: string | null
  ) {
    setLinkingRowId(lineId);
    try {
      await saveLine(lineId, { linked_issue_id: linkedIssueId });
    } finally {
      setLinkingRowId(null);
    }
  }

  async function convertLineToFreeText(lineId: string) {
    await saveLine(lineId, { issue_id: null });
  }

  async function deleteLine(lineId: string) {
    if (!report.is_editable) {
      return;
    }

    try {
      setLineSaving(true);
      setError("");

      if (await shouldSaveLinesLocally()) {
        const updated = await deleteLocalLine(clientReportUuid, lineId);

        if (!updated) {
          throw new Error("מחיקת שורה במכשיר נכשלה");
        }

        onReportChange(localVisitReportToView(updated) as VisitReport);
      } else {
        const serverId = report.server_report_id;
        if (!serverId) {
          throw new Error("אין מזהה שרת לדוח");
        }

        const response = await apiFetch(
          `/field-reports/visits/${serverId}/lines/${lineId}`,
          { method: "DELETE" }
        );

        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          throw new Error(
            payload.error?.message
              || payload.message
              || "מחיקת שורה נכשלה"
          );
        }

        onReportChange({
          ...report,
          lines: report.lines.filter((line) => line.id !== lineId),
        });
      }
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "מחיקת שורה נכשלה"
      );
    } finally {
      setLineSaving(false);
    }
  }

  return (
    <div className="space-y-6 md:space-y-8">
      <div className="flex flex-wrap items-center gap-2.5 text-sm text-zinc-600">
        <Badge>{report.status_label_he}</Badge>
        {useLocalReports ? (
          <span className="rounded-full bg-amber-100 px-3 py-1 text-amber-900 dark:bg-amber-950/50 dark:text-amber-100">
            {dataSourceMode === "local-only"
              ? "אופליין - נשמר במכשיר"
              : "נשמר במכשיר"}
          </span>
        ) : (
          <span className="text-zinc-500">מחובר לשרת</span>
        )}
        {report.catalog_version ? (
          <span>קטלוג: {report.catalog_version}</span>
        ) : null}
        {saveState === "saving" ? (
          <span className="text-zinc-500">שומר פרטי כותרת...</span>
        ) : null}
        {saveState === "saved" ? (
          <span className="text-emerald-700">נשמר</span>
        ) : null}
        {saveState === "offline" ? (
          <span className="text-amber-800">נשמר במכשיר - יסונכרן ברשת</span>
        ) : null}
        {useLocalReports && lineAutosaveState === "saving" ? (
          <span className="text-zinc-500">שומר שורות...</span>
        ) : null}
        {useLocalReports && lineAutosaveState === "saved" ? (
          <span className="text-emerald-700">שורות נשמרו במכשיר</span>
        ) : null}
      </div>

      {report.catalog_sync?.is_current === false &&
      report.catalog_sync.message ? (
        <p className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
          {report.catalog_sync.message}
        </p>
      ) : null}

      {catalogLineWarnings > 0 && !isSupervisionReport ? (
        <p className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-200">
          {catalogLineWarnings} שורות עם אזהרת מפרט - בדוק לפני סגירת הדוח.
        </p>
      ) : null}

      {isSupervisionReport && supervisionChecklistBlock ? (
        <SupervisionChecklistEditor
          block={supervisionChecklistBlock}
          reportId={report.server_report_id ?? clientReportUuid}
          inspectMode={inspectMode}
          disabled={!report.is_editable}
          onChange={updateSupervisionChecklistBlock}
        />
      ) : null}

      {!isSupervisionReport ? (
        <>
      <ReportProjectMetadataSection
        metadata={headerFields.project_metadata}
        disabled={!report.is_editable}
        onChange={(project_metadata) =>
          setHeaderFields((current) => ({
            ...current,
            project_metadata,
          }))
        }
      />

      <ReportStakeholdersSection
        stakeholders={headerFields.stakeholders}
        mainSuppliers={headerFields.main_suppliers}
        disabled={!report.is_editable}
        projectId={report.project_id}
        onChange={({ stakeholders, main_suppliers }) =>
          setHeaderFields((current) =>
            patchHeaderFieldsStakeholders(
              current,
              { stakeholders, main_suppliers },
              report.visit_type
            )
          )
        }
      />

      <section className="space-y-4 rounded-xl border border-zinc-200 p-4 md:p-5">
        <h2 className="text-lg font-semibold">פרטי כותרת הדוח</h2>
        <div className="grid gap-3 md:grid-cols-2">
          <HeaderField
            label="כתובת אתר"
            value={headerFields.site_address}
            disabled={!report.is_editable}
            onChange={(value) =>
              setHeaderFields((current) => ({
                ...current,
                site_address: value,
              }))
            }
          />
        </div>
        {report.is_editable ? (
          <Button
            variant="secondary"
            size="lg"
            className={FR_TOUCH_BUTTON}
            disabled={saving || (!canCallVisitReportApi && !useLocalReports)}
            onClick={() => void saveHeaderFields()}
          >
            {saving ? "שומר..." : "שמור עכשיו"}
          </Button>
        ) : null}
      </section>

      <ReportBlocksManager
        blocks={headerFields.blocks}
        visitType={report.visit_type}
        disabled={!report.is_editable}
        projectId={report.project_id}
        organizationId={organizationId}
        reportId={report.server_report_id ?? clientReportUuid}
        inspectMode={inspectMode}
        linkingRowId={linkingRowId}
        onLinkFindingRow={linkFindingRow}
        hasExplicitBlocks={hasExplicitBlocks}
        findingsLinesPanel={
          <ReportFindingsLinesPanel
            lines={report.lines}
            editable={report.is_editable}
            lineSaving={lineSaving}
            linkingRowId={linkingRowId}
            reportId={report.server_report_id ?? clientReportUuid}
            projectId={report.project_id}
            organizationId={organizationId}
            catalogOpen={catalogOpen}
            catalogFamilies={catalogFamilies}
            catalogCategories={catalogCategories}
            catalogIssues={catalogIssues}
            catalogLoading={catalogLoading}
            catalogError={catalogError}
            catalogPickerRef={catalogPickerRef}
            pendingLineGroup={pendingLineGroup}
            newLine={newLine}
            lineAutosave={useLocalReports}
            onLoadCatalog={() => void loadCatalog()}
            onCloseCatalog={() => {
              setCatalogOpen(false);
              setCatalogError("");
            }}
            onConfirmCatalog={(issue) => void addCatalogLine(issue)}
            onPhotoCaptured={addQuickFindingFromPhoto}
            onPendingLineGroupChange={setPendingLineGroup}
            onNewLineChange={(patch) =>
              setNewLine((current) => ({ ...current, ...patch }))
            }
            onAddFreeLine={addFreeLine}
            onSaveLine={saveLine}
            onLinkRow={linkFindingRow}
            onConvertToFreeText={convertLineToFreeText}
            onDeleteLine={deleteLine}
            onPhotosChange={updateLinePhotosState}
          />
        }
        onChange={(blocks) =>
          setHeaderFields((current) =>
            patchHeaderFieldsBlocks(current, blocks, report.visit_type)
          )
        }
      />

      <ReportFixedBlocksSection
        fields={headerFields}
        visitType={report.visit_type}
        visitDate={report.visit_date}
        disabled={!report.is_editable}
        onChange={setHeaderFields}
      />
        </>
      ) : null}

      {error ? <p className="text-sm text-red-600">{error}</p> : null}
    </div>
  );
}

function HeaderField({
  label,
  value,
  disabled,
  onChange,
}: {
  label: string;
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block space-y-1 text-sm">
      <span className="font-medium">{label}</span>
      <input
        className={FR_TOUCH_INPUT}
        value={normalizeOptionalTextInput(value)}
        disabled={disabled}
        placeholder={UNSPECIFIED_FIELD_LABEL_HE}
        onChange={(event) =>
          onChange(optionalTextForSave(event.target.value) ?? "")
        }
      />
    </label>
  );
}

