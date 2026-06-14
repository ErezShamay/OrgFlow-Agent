"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, startTransition, useCallback, useEffect, useMemo, useState } from "react";

import ApartmentPicker, {
  type ApartmentSelection,
} from "@/components/field-reports/supervision/ApartmentPicker";
import ConstructionStagePicker from "@/components/field-reports/supervision/ConstructionStagePicker";
import PublicAreaPicker from "@/components/field-reports/supervision/PublicAreaPicker";
import VisitScopePicker from "@/components/field-reports/supervision/VisitScopePicker";
import Button from "@/components/ui/Button";
import { useAuth } from "@/contexts/AuthContext";
import { useFieldReportDataSource } from "@/hooks/useFieldReportDataSource";
import { useFieldReportModule } from "@/hooks/useFieldReportModule";
import { useProjectWorkspace } from "@/hooks/useProjectWorkspace";
import {
  fieldReportDataSourceModeLabelHe,
} from "@/lib/field-reports/data-source";
import { fetchProjectPrefill } from "@/lib/field-reports/new-report-form";
import {
  hydrateOfflinePrepBundle,
  isOfflinePrepValid,
  type OfflinePrepBundle,
} from "@/lib/field-reports/offline-store";
import { listApartmentsFromOfflineBundle } from "@/lib/field-reports/offline-prep-apartments";
import { projectPrefillSourceFromRecord } from "@/lib/field-reports/project-header-prefill";
import { isExpired } from "@/lib/field-reports/repositories/catalog-repository";
import { fieldReportDetailPath } from "@/lib/field-reports/routes";
import type {
  ConstructionStage,
  PublicAreaId,
  SupervisionCatalog,
  VisitScope,
} from "@/lib/field-reports/schema/types";
import {
  createSupervisionLocalReport,
  fetchSupervisionCatalogFromApi,
  loadSupervisionCatalogFromOfflineBundle,
  syncNewVisitReportToServer,
} from "@/lib/field-reports/supervision-new-report";

export default function ProjectSupervisionNewReportPage() {
  const params = useParams();
  const projectId = String(params.id ?? "");
  const router = useRouter();
  const { profile } = useAuth();
  const { project, loading: projectLoading } = useProjectWorkspace(projectId);
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

  const [catalog, setCatalog] = useState<SupervisionCatalog | null>(null);
  const [offlinePrepBundle, setOfflinePrepBundle] =
    useState<OfflinePrepBundle | null>(null);
  const [catalogVersion, setCatalogVersion] = useState<string | null>(null);
  const [organizationProfileSnapshot, setOrganizationProfileSnapshot] =
    useState<Record<string, unknown> | null>(null);
  const [constructionStage, setConstructionStage] =
    useState<ConstructionStage | null>(null);
  const [visitScope, setVisitScope] = useState<VisitScope | null>(null);
  const [apartmentSelection, setApartmentSelection] =
    useState<ApartmentSelection | null>(null);
  const [publicAreaId, setPublicAreaId] = useState<PublicAreaId | null>(null);
  const [visitDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const offlineApartments = useMemo(
    () => listApartmentsFromOfflineBundle(offlinePrepBundle, projectId),
    [offlinePrepBundle, projectId]
  );

  const loadCatalog = useCallback(async () => {
    if (!organizationId) {
      return;
    }

    try {
      setLoading(true);
      setError("");

      const bundle = await hydrateOfflinePrepBundle(organizationId);
      setOfflinePrepBundle(bundle);
      const catalogReady =
        bundle && isOfflinePrepValid(bundle) && !isExpired(bundle);

      if (useLocalCatalog) {
        if (!catalogReady || !bundle) {
          throw new Error(
            "אין חבילת הכנה לא מקוון תקפה. חזור לפרויקט ובצע «הכנה לא מקוון» כשיש רשת."
          );
        }

        const parsed = loadSupervisionCatalogFromOfflineBundle(bundle);
        setCatalog(parsed);
        setCatalogVersion(bundle.catalog_version ?? parsed.catalog_version ?? null);
        setOrganizationProfileSnapshot(
          (bundle.organization_profile as Record<string, unknown>) ?? null
        );
        return;
      }

      if (catalogReady && bundle) {
        try {
          const parsed = loadSupervisionCatalogFromOfflineBundle(bundle);
          setCatalog(parsed);
          setCatalogVersion(bundle.catalog_version ?? parsed.catalog_version ?? null);
          setOrganizationProfileSnapshot(
            (bundle.organization_profile as Record<string, unknown>) ?? null
          );
          return;
        } catch {
          // fall through to API
        }
      }

      if (canCallVisitReportApi) {
        const parsed = await fetchSupervisionCatalogFromApi();
        setCatalog(parsed);
        setCatalogVersion(parsed.catalog_version ?? null);
        setOrganizationProfileSnapshot(null);
        return;
      }

      throw new Error(
        "אין קטלוג supervision זמין. בצע «הכנה לא מקוון» כשיש רשת."
      );
    } catch (err: unknown) {
      setCatalog(null);
      setOfflinePrepBundle(null);
      setError(
        err instanceof Error ? err.message : "טעינת קטלוג supervision נכשלה"
      );
    } finally {
      setLoading(false);
    }
  }, [organizationId, useLocalCatalog, canCallVisitReportApi]);

  useEffect(() => {
    if (moduleLoading || !isEnabled || !organizationId) {
      return;
    }

    startTransition(() => {
      void loadCatalog();
    });
  }, [moduleLoading, isEnabled, organizationId, loadCatalog]);

  useEffect(() => {
    if (visitScope !== "APARTMENT") {
      setApartmentSelection(null);
    }
    if (visitScope !== "PUBLIC_AREA") {
      setPublicAreaId(null);
    }
  }, [visitScope]);

  const canSubmit =
    Boolean(catalog)
    && Boolean(constructionStage)
    && Boolean(visitScope)
    && (visitScope === "APARTMENT"
      ? Boolean(apartmentSelection?.apartmentNumber.trim())
      : Boolean(publicAreaId));

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (
      !organizationId
      || !projectId
      || !catalog
      || !constructionStage
      || !visitScope
      || !canSubmit
    ) {
      setError("יש להשלים את כל השלבים");
      return;
    }

    try {
      setSubmitting(true);
      setError("");
      setNotice("");

      let projectPrefill = project
        ? projectPrefillSourceFromRecord(project as Record<string, unknown>)
        : null;

      if (!projectPrefill && canCallVisitReportApi) {
        projectPrefill = await fetchProjectPrefill(projectId);
      }

      const localReport = await createSupervisionLocalReport({
        organizationId,
        userId: profile?.id ?? null,
        projectId,
        projectName: project?.project_name ?? null,
        visitDate,
        catalog,
        constructionStage,
        visitScope,
        apartmentId:
          visitScope === "APARTMENT"
            ? apartmentSelection?.apartmentId ?? null
            : null,
        apartmentNumber:
          visitScope === "APARTMENT"
            ? apartmentSelection?.apartmentNumber ?? null
            : null,
        ownerName:
          visitScope === "APARTMENT"
            ? apartmentSelection?.ownerName ?? null
            : null,
        adHocApartment:
          visitScope === "APARTMENT"
            ? apartmentSelection?.adHocApartment ?? false
            : false,
        publicAreaId: visitScope === "PUBLIC_AREA" ? publicAreaId ?? undefined : undefined,
        catalogVersion,
        organizationProfileSnapshot,
        projectPrefill,
      });

      if (canCallVisitReportApi) {
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

  if (moduleLoading || projectLoading || (isEnabled && loading)) {
    return (
      <div className="of-container mx-auto max-w-xl p-8 text-sm text-zinc-500">
        טוען...
      </div>
    );
  }

  if (!isEnabled) {
    return (
      <div className="of-container mx-auto max-w-xl space-y-4 p-8">
        <h1 className="of-page-title text-2xl">הפקת דוח</h1>
        <p className="text-sm text-zinc-600">
          מודול הפקת דוחות אינו מופעל עבור הארגון.
        </p>
        <Link
          href={`/projects/${encodeURIComponent(projectId)}`}
          className="text-sm text-brand hover:underline"
        >
          חזרה לפרויקט
        </Link>
      </div>
    );
  }

  return (
    <div className="of-container mx-auto max-w-xl space-y-6 p-4 md:p-8">
      <header className="space-y-2">
        <Link
          href={`/projects/${encodeURIComponent(projectId)}`}
          className="text-sm text-brand hover:underline"
        >
          ← {project?.project_name ?? "פרויקט"}
        </Link>
        <h1 className="of-page-title text-2xl">הפקת דוח</h1>
        <p className="of-page-desc text-sm">
          בחר שלב, סוג ביקור ויחידה — ואז התחל את הצ&apos;קליסט.
        </p>
        <p className="text-xs text-zinc-500">
          {fieldReportDataSourceModeLabelHe(dataSourceMode)}
          {pinging ? " · בודק חיבור..." : ""}
        </p>
      </header>

      <form onSubmit={(event) => void handleSubmit(event)} className="space-y-6">
        <ConstructionStagePicker
          value={constructionStage}
          onChange={setConstructionStage}
        />

        {constructionStage ? (
          <VisitScopePicker value={visitScope} onChange={setVisitScope} />
        ) : null}

        {visitScope === "APARTMENT" ? (
          <ApartmentPicker
            projectId={projectId}
            value={apartmentSelection}
            onChange={setApartmentSelection}
            canLoadFromApi={canCallVisitReportApi}
            offlineApartments={offlineApartments}
          />
        ) : null}

        {visitScope === "PUBLIC_AREA" ? (
          <PublicAreaPicker value={publicAreaId} onChange={setPublicAreaId} />
        ) : null}

        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        {notice ? (
          <p className="text-sm text-amber-700 dark:text-amber-300">{notice}</p>
        ) : null}

        <div className="flex flex-wrap gap-3">
          <Button type="submit" disabled={submitting || !canSubmit}>
            {submitting ? "יוצר..." : "התחל ביקור"}
          </Button>
          <Link href={`/projects/${encodeURIComponent(projectId)}`}>
            <Button variant="secondary" type="button">
              ביטול
            </Button>
          </Link>
        </div>
      </form>
    </div>
  );
}
