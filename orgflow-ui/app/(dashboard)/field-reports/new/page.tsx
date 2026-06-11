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
import { useAuth } from "@/contexts/AuthContext";
import { useFieldReportDataSource } from "@/hooks/useFieldReportDataSource";
import { useFieldReportModule } from "@/hooks/useFieldReportModule";
import {
  fieldReportDataSourceModeLabelHe,
} from "@/lib/field-reports/data-source";
import {
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

export default function NewFieldVisitReportPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedProjectId = searchParams.get("project");
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
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const applyFormDefaults = useCallback(
    (
      projectList: NewReportProject[],
      typeList: NewReportVisitType[]
    ) => {
      setProjects(projectList);
      setVisitTypes(typeList);

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
    [preselectedProjectId]
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

    startTransition(() => {
      void loadFormData();
    });
  }, [moduleLoading, isEnabled, organizationId, loadFormData]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (!organizationId || !projectId || !visitType || !visitDate) {
      setError("יש למלא את כל השדות");
      return;
    }

    const selectedProject = projects.find(
      (project) => project.id === projectId
    );
    const selectedVisitType = visitTypes.find(
      (type) => type.code === visitType
    );

    try {
      setSubmitting(true);
      setError("");
      setNotice("");

      let projectPrefill = selectedProject?.prefill ?? null;
      if (!projectPrefill && canCallVisitReportApi) {
        projectPrefill = await fetchProjectPrefill(projectId);
      }

      const localReport = await createLocalVisitReport({
        organizationId,
        userId: profile?.id ?? null,
        projectId,
        projectName: selectedProject?.project_name ?? null,
        visitType,
        visitTypeLabelHe: selectedVisitType?.label_he ?? null,
        visitDate,
        catalogVersion,
        organizationProfileSnapshot,
        projectPrefill,
      });

      if (canCallVisitReportApi) {
        const syncResult = await syncNewVisitReportToServer(localReport);
        if (!syncResult.ok) {
          setNotice(
            `הדוח נשמר במכשיר. ${syncResult.message}`
          );
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
        <h1 className="of-page-title text-2xl">דוח ביקור חדש</h1>
        <p className="text-sm text-zinc-600">
          מודול הפקת דוחות אינו מופעל עבור הארגון.
        </p>
        <Link href="/field-reports" className="text-sm text-brand hover:underline">
          חזרה
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
          ← הדוחות שלי
        </Link>
        <h1 className="of-page-title text-2xl">דוח ביקור חדש</h1>
        <p className="of-page-desc text-sm">
          דוח שבועי אחד לפרויקט - אם קיים דוח בעבודה, יש להמשיך אותו.
        </p>
        <p className="text-xs text-zinc-500">
          {fieldReportDataSourceModeLabelHe(dataSourceMode)}
          {pinging ? " · בודק חיבור..." : ""}
        </p>
      </header>

      <form onSubmit={(event) => void handleSubmit(event)} className="space-y-4">
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

        {error ? (
          <p className="text-sm text-red-600">{error}</p>
        ) : null}

        {notice ? (
          <p className="text-sm text-amber-700 dark:text-amber-300">{notice}</p>
        ) : null}

        <div className="flex flex-wrap gap-3">
          <Button type="submit" disabled={submitting}>
            {submitting ? "יוצר..." : "צור דוח"}
          </Button>
          <Link href="/field-reports">
            <Button variant="secondary" type="button">
              ביטול
            </Button>
          </Link>
        </div>
      </form>
    </div>
  );
}
