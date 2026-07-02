"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  FormEvent,
  startTransition,
  useCallback,
  useEffect,
  useState,
} from "react";

import Button from "@/components/ui/Button";
import CancelReportCreationDialog from "@/components/field-reports/CancelReportCreationDialog";
import { useAuth } from "@/contexts/AuthContext";
import { useFieldReportDataSource } from "@/hooks/useFieldReportDataSource";
import { useFieldReportModule } from "@/hooks/useFieldReportModule";
import {
  fieldReportDataSourceModeLabelHe,
} from "@/lib/field-reports/data-source";
import {
  readModularTemplateDraft,
  type ModularTemplateDraft,
} from "@/lib/field-reports/modular-template-draft";
import {
  CLIENT_ONLY_PROJECT_ID,
  createLocalVisitReport,
  fetchProjectPrefill,
  parseNewReportFormFromApi,
  parseNewReportFormFromCatalog,
  syncNewVisitReportToServer,
  type NewReportProject,
  type NewReportVisitType,
} from "@/lib/field-reports/new-report-form";
import {
  hydrateOfflinePrepBundle,
  isOfflinePrepValid,
} from "@/lib/field-reports/offline-store";
import { fieldReportDetailPath } from "@/lib/field-reports/routes";
import { isExpired } from "@/lib/field-reports/repositories/catalog-repository";
import { findTemplateLibraryItem } from "@/lib/field-reports/template-library";

export default function NewFieldVisitReportPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedProjectId = searchParams.get("project")?.trim() ?? "";
  const templateId = searchParams.get("template")?.trim() ?? "";
  const visitTypeFromQuery = searchParams.get("visit_type")?.trim() ?? "";
  const sourceFromQuery = searchParams.get("source")?.trim() ?? "";
  const modularTemplateKey = searchParams.get("modular_template_key")?.trim() ?? "";
  const clientNameFromQuery = searchParams.get("client_name")?.trim() ?? "";
  const clientAddressFromQuery = searchParams.get("client_address")?.trim() ?? "";
  const wizardMode = Boolean(templateId);
  const { profile } = useAuth();
  const {
    status: moduleStatus,
    isEnabled,
    loading: moduleLoading,
  } = useFieldReportModule();
  const organizationId = moduleStatus?.organization_id || "";
  const {
    useLocalCatalog,
    canCallVisitReportApi,
    mode: dataSourceMode,
    pinging,
  } = useFieldReportDataSource();

  const [projects, setProjects] = useState<NewReportProject[]>([]);
  const [visitTypes, setVisitTypes] = useState<NewReportVisitType[]>([]);
  const [catalogVersion, setCatalogVersion] = useState<string | null>(null);
  const [organizationProfileSnapshot, setOrganizationProfileSnapshot] =
    useState<Record<string, unknown> | null>(null);
  const [projectId, setProjectId] = useState("");
  const [visitType, setVisitType] = useState("");
  const [visitDate, setVisitDate] = useState(
    () => new Date().toISOString().slice(0, 10)
  );
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [modularTemplateDraft, setModularTemplateDraft] =
    useState<ModularTemplateDraft | null>(null);

  const templateItem = templateId ? findTemplateLibraryItem(templateId) : null;

  useEffect(() => {
    if (!wizardMode || !modularTemplateKey) {
      setModularTemplateDraft(null);
      return;
    }
    setModularTemplateDraft(readModularTemplateDraft(modularTemplateKey));
  }, [wizardMode, modularTemplateKey]);

  const applyFormDefaults = useCallback(
    (
      projectList: NewReportProject[],
      typeList: NewReportVisitType[]
    ) => {
      setProjects(projectList);
      setVisitTypes(typeList);

      if (wizardMode) {
        if (sourceFromQuery === "client") {
          setProjectId(CLIENT_ONLY_PROJECT_ID);
        } else if (
          preselectedProjectId
          && projectList.some((project) => project.id === preselectedProjectId)
        ) {
          setProjectId(preselectedProjectId);
        }

        const resolvedVisitType =
          modularTemplateDraft?.visitType
          || visitTypeFromQuery
          || templateItem?.visitType
          || typeList[0]?.code
          || "";
        if (resolvedVisitType) {
          setVisitType(resolvedVisitType);
        }
        return;
      }

      const defaultProjectId =
        preselectedProjectId
        && projectList.some(
          (project) => project.id === preselectedProjectId
        )
          ? preselectedProjectId
          : projectList[0]?.id;

      if (defaultProjectId) {
        setProjectId(defaultProjectId);
      }

      const firstType = typeList[0]?.code;
      if (firstType) {
        setVisitType(firstType);
      }
    },
    [
      preselectedProjectId,
      wizardMode,
      sourceFromQuery,
      visitTypeFromQuery,
      templateItem?.visitType,
      modularTemplateDraft?.visitType,
    ]
  );

  const loadFormData = useCallback(async () => {
    if (!organizationId) {
      return;
    }

    try {
      setLoading(true);
      setError("");
      setNotice("");

      const bundle = await hydrateOfflinePrepBundle(organizationId);
      const catalogReady =
        bundle && isOfflinePrepValid(bundle) && !isExpired(bundle);

      if (useLocalCatalog) {
        if (!catalogReady) {
          throw new Error(
            "אין חבילת הכנה לא מקוון תקפה. חזור לרשימת הדוחות ובצע «הכנה לא מקוון»."
          );
        }

        const parsed = parseNewReportFormFromCatalog(bundle);
        if (!parsed.projects.length || !parsed.visitTypes.length) {
          throw new Error(
            "חבילת ההכנה חסרה פרויקטים או סוגי ביקור. בצע הכנה לא מקוון מחדש."
          );
        }

        setCatalogVersion(bundle.catalog_version ?? null);
        setOrganizationProfileSnapshot(
          (bundle.organization_profile as Record<string, unknown>)
          ?? null
        );
        applyFormDefaults(parsed.projects, parsed.visitTypes);
        return;
      }

      if (catalogReady) {
        const parsed = parseNewReportFormFromCatalog(bundle);
        if (parsed.projects.length && parsed.visitTypes.length) {
          setCatalogVersion(bundle.catalog_version ?? null);
          setOrganizationProfileSnapshot(
            (bundle.organization_profile as Record<string, unknown>)
            ?? null
          );
          applyFormDefaults(parsed.projects, parsed.visitTypes);
          return;
        }
      }

      const fromApi = await parseNewReportFormFromApi();
      setCatalogVersion(null);
      setOrganizationProfileSnapshot(null);
      applyFormDefaults(fromApi.projects, fromApi.visitTypes);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "טעינת נתוני הטופס נכשלה"
      );
    } finally {
      setLoading(false);
    }
  }, [organizationId, useLocalCatalog, applyFormDefaults]);

  useEffect(() => {
    if (moduleLoading || !isEnabled || !organizationId) {
      return;
    }

    if (preselectedProjectId && !wizardMode) {
      router.replace(
        `/projects/${encodeURIComponent(preselectedProjectId)}/field-reports/new`
      );
      return;
    }

    startTransition(() => {
      void loadFormData();
    });
  }, [
    moduleLoading,
    isEnabled,
    organizationId,
    loadFormData,
    preselectedProjectId,
    wizardMode,
    router,
  ]);

  useEffect(() => {
    if (!wizardMode || !modularTemplateDraft) {
      return;
    }
    if (modularTemplateDraft.visitType) {
      setVisitType(modularTemplateDraft.visitType);
    }
  }, [wizardMode, modularTemplateDraft]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (!organizationId || !visitType || !visitDate) {
      setError("יש למלא את כל השדות");
      return;
    }

    const isClientOnly = sourceFromQuery === "client";
    if (!isClientOnly && !projectId) {
      setError("יש לבחור פרויקט");
      return;
    }

    if (isClientOnly && (!clientNameFromQuery || !clientAddressFromQuery)) {
      setError("חסרים פרטי לקוח");
      return;
    }

    const selectedProject = projects.find(
      (project) => project.id === projectId
    );
    const selectedVisitType = visitTypes.find(
      (type) => type.code === visitType
    );
    const templateLabel =
      modularTemplateDraft?.templateLabel
      || templateItem?.label_he
      || selectedVisitType?.label_he
      || null;

    try {
      setSubmitting(true);
      setError("");
      setNotice("");

      let projectPrefill = selectedProject?.prefill ?? null;
      if (!projectPrefill && canCallVisitReportApi && !isClientOnly && projectId) {
        projectPrefill = await fetchProjectPrefill(projectId);
      }

      const localReport = await createLocalVisitReport({
        organizationId,
        userId: profile?.id ?? null,
        projectId: isClientOnly ? CLIENT_ONLY_PROJECT_ID : projectId,
        projectName: isClientOnly
          ? clientNameFromQuery
          : selectedProject?.project_name ?? null,
        visitType,
        visitTypeLabelHe: templateLabel,
        visitDate,
        catalogVersion,
        organizationProfileSnapshot,
        projectPrefill: isClientOnly ? null : projectPrefill,
        clientName: isClientOnly ? clientNameFromQuery : null,
        clientAddress: isClientOnly ? clientAddressFromQuery : null,
        modularTemplateDraft,
      });

      if (canCallVisitReportApi && !isClientOnly) {
        const syncResult = await syncNewVisitReportToServer(localReport);
        if (!syncResult.ok) {
          setNotice(`הדוח נשמר במכשיר. ${syncResult.message}`);
        }
      }

      router.push(fieldReportDetailPath(localReport.client_report_uuid));
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "יצירת הדוח נכשלה"
      );
    } finally {
      setSubmitting(false);
    }
  }

  function handleConfirmCancel() {
    setCancelDialogOpen(false);
    router.push("/field-reports");
  }

  const selectedProjectName =
    projects.find((project) => project.id === projectId)?.project_name
    ?? (sourceFromQuery === "client" ? clientNameFromQuery : "");

  if (moduleLoading || (isEnabled && loading)) {
    return (
      <div className="of-container mx-auto max-w-xl p-8 text-sm text-zinc-500">
        טוען...
      </div>
    );
  }

  if (!isEnabled) {
    return (
      <div className="of-container mx-auto max-w-xl space-y-4 p-8">
        <h1 className="of-page-title text-2xl">יצירת דוח</h1>
        <p className="text-sm text-zinc-600">
          מודול יצירת דוחות אינו מופעל עבור הארגון.
        </p>
        <Link href="/field-reports" className="text-sm text-brand hover:underline">
          חזרה
        </Link>
      </div>
    );
  }

  if (wizardMode && !templateItem) {
    return (
      <div className="of-container mx-auto max-w-xl space-y-4 p-8">
        <p className="text-sm text-red-600">תבנית לא נמצאה.</p>
        <Link href="/field-reports" className="text-sm text-brand hover:underline">
          חזרה ליצירת דוחות
        </Link>
      </div>
    );
  }

  return (
    <div className="of-container mx-auto max-w-xl space-y-6 p-8">
      <header className="space-y-2">
        <Link
          href="/field-reports"
          className="text-sm text-brand hover:underline"
        >
          ← יצירת דוחות
        </Link>
        <h1 className="of-page-title text-2xl">יצירת דוח</h1>
        <p className="of-page-desc text-sm">
          {wizardMode
            ? "אשר את פרטי הדוח והתבנית שנבחרו וצור את הדוח."
            : "דוח שבועי אחד לפרויקט - אם קיים דוח בעבודה, יש להמשיך אותו."}
        </p>
        <p className="text-xs text-zinc-500">
          {fieldReportDataSourceModeLabelHe(dataSourceMode)}
          {pinging ? " · בודק חיבור..." : ""}
        </p>
      </header>

      {wizardMode ? (
        <section className="space-y-3 rounded-xl border border-zinc-200 bg-zinc-50 p-4 text-sm dark:border-zinc-700 dark:bg-zinc-800/40">
          <p className="font-medium">תצוגה מקדימה</p>
          <p>
            מקור: {sourceFromQuery === "client" ? "ללא פרויקט" : "עם פרויקט"}
          </p>
          {sourceFromQuery === "client" ? (
            <>
              <p>לקוח: {clientNameFromQuery}</p>
              <p>כתובת: {clientAddressFromQuery}</p>
            </>
          ) : (
            <p>פרויקט: {selectedProjectName || "-"}</p>
          )}
          <p>תבנית: {templateItem?.label_he}</p>
          {modularTemplateDraft ? (
            <ul className="list-disc space-y-1 pr-5 text-zinc-600 dark:text-zinc-300">
              {modularTemplateDraft.blocks
                .filter((block) => block.enabled)
                .map((block) => (
                  <li key={block.id}>{block.title_he}</li>
                ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      <form onSubmit={(event) => void handleSubmit(event)} className="space-y-4">
        {!wizardMode ? (
          <>
            <label className="block space-y-1 text-sm">
              <span className="font-medium">פרויקט</span>
              <select
                className="of-input w-full"
                value={projectId}
                onChange={(event) => setProjectId(event.target.value)}
                required
              >
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.project_name}
                  </option>
                ))}
              </select>
            </label>

            <label className="block space-y-1 text-sm">
              <span className="font-medium">סוג ביקור</span>
              <select
                className="of-input w-full"
                value={visitType}
                onChange={(event) => setVisitType(event.target.value)}
                required
              >
                {visitTypes.map((type) => (
                  <option key={type.code} value={type.code}>
                    {type.label_he}
                  </option>
                ))}
              </select>
            </label>
          </>
        ) : null}

        <label className="block space-y-1 text-sm">
          <span className="font-medium">תאריך ביקור</span>
          <input
            type="date"
            className="of-input w-full"
            value={visitDate}
            onChange={(event) => setVisitDate(event.target.value)}
            required
          />
        </label>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        {notice ? (
          <p className="text-sm text-amber-700 dark:text-amber-300">{notice}</p>
        ) : null}

        <div className="flex flex-wrap gap-3">
          <Button type="submit" disabled={submitting}>
            {submitting ? "יוצר..." : "צור דוח"}
          </Button>
          <Button
            variant="secondary"
            type="button"
            onClick={() => setCancelDialogOpen(true)}
            disabled={submitting}
          >
            ביטול
          </Button>
        </div>
      </form>

      <CancelReportCreationDialog
        open={cancelDialogOpen}
        onStay={() => setCancelDialogOpen(false)}
        onConfirmCancel={handleConfirmCancel}
      />
    </div>
  );
}
