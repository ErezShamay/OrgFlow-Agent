"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { FormEvent, startTransition, useCallback, useEffect, useMemo, useState } from "react";

import ApartmentPicker, {
  type ApartmentSelection,
} from "@/components/field-reports/supervision/ApartmentPicker";
import CancelReportCreationDialog from "@/components/field-reports/CancelReportCreationDialog";
import ConstructionStagePicker from "@/components/field-reports/supervision/ConstructionStagePicker";
import DocumentKindPicker from "@/components/field-reports/supervision/DocumentKindPicker";
import PublicAreaPicker from "@/components/field-reports/supervision/PublicAreaPicker";
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
import { listProjectApartments } from "@/lib/apartments/api";
import { projectPrefillSourceFromRecord } from "@/lib/field-reports/project-header-prefill";
import { isExpired } from "@/lib/field-reports/repositories/catalog-repository";
import { fieldReportDetailPath } from "@/lib/field-reports/routes";
import {
  type DocumentWizardKind,
  documentTypeFromWizardKind,
  isWeeklyDocumentWizardKind,
  visitScopeFromDocumentWizardKind,
} from "@/lib/field-reports/document-wizard";
import type {
  ConstructionStage,
  PublicAreaId,
  SupervisionCatalog,
} from "@/lib/field-reports/schema/types";
import {
  createSupervisionLocalReport,
  fetchSupervisionCatalogFromApi,
  hasSupervisionNewReportApartmentPrefill,
  hasSupervisionNewReportPublicAreaPrefill,
  loadSupervisionCatalogFromOfflineBundle,
  parseSupervisionNewReportPrefill,
  parseSupervisionNewReportPublicAreaPrefill,
  resolveApartmentSelectionFromPrefill,
  syncNewVisitReportToServer,
} from "@/lib/field-reports/supervision-new-report";

export default function ProjectSupervisionNewReportPage() {
  const params = useParams();
  const projectId = String(params.id ?? "");
  const router = useRouter();
  const searchParams = useSearchParams();
  const apartmentPrefill = useMemo(
    () => parseSupervisionNewReportPrefill(searchParams),
    [searchParams]
  );
  const publicAreaPrefill = useMemo(
    () => parseSupervisionNewReportPublicAreaPrefill(searchParams),
    [searchParams]
  );
  const hasApartmentPrefill = hasSupervisionNewReportApartmentPrefill(
    apartmentPrefill
  );
  const hasPublicAreaPrefill = hasSupervisionNewReportPublicAreaPrefill(
    publicAreaPrefill
  );
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
  const [documentKind, setDocumentKind] = useState<DocumentWizardKind | null>(
    null
  );
  const visitScope = documentKind
    ? visitScopeFromDocumentWizardKind(documentKind)
    : null;
  const [apartmentSelection, setApartmentSelection] =
    useState<ApartmentSelection | null>(null);
  const [publicAreaId, setPublicAreaId] = useState<PublicAreaId | null>(null);
  const [visitDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
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
      const catalogReady =
        Boolean(bundle)
        && isOfflinePrepValid(bundle)
        && !isExpired(bundle);

      setOfflinePrepBundle(bundle);

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
          if (useLocalCatalog) {
            throw new Error(
              "אין הכנה לא מקוון. התחבר לרשת ובצע «הכנה לא מקוון» מרשימת הדוחות."
            );
          }
        }
      }

      if (useLocalCatalog) {
        throw new Error(
          "אין הכנה לא מקוון. התחבר לרשת ובצע «הכנה לא מקוון» מרשימת הדוחות."
        );
      }

      if (canCallVisitReportApi) {
        const parsed = await fetchSupervisionCatalogFromApi();
        setCatalog(parsed);
        setCatalogVersion(parsed.catalog_version ?? null);
        setOrganizationProfileSnapshot(null);
        return;
      }

      throw new Error(
        "אין קטלוג supervision זמין. התחבר לרשת ונסה שוב."
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
  }, [
    organizationId,
    projectId,
    useLocalCatalog,
    canCallVisitReportApi,
  ]);

  useEffect(() => {
    if (moduleLoading || !isEnabled || !organizationId) {
      return;
    }

    startTransition(() => {
      void loadCatalog();
    });
  }, [moduleLoading, isEnabled, organizationId, loadCatalog]);

  useEffect(() => {
    if (documentKind !== "WEEKLY_APARTMENT") {
      if (!hasApartmentPrefill) {
        setApartmentSelection(null);
      }
    }
    if (documentKind !== "WEEKLY_PUBLIC_AREA") {
      setPublicAreaId(null);
    }
    if (!isWeeklyDocumentWizardKind(documentKind)) {
      setConstructionStage(null);
    }
  }, [documentKind, hasApartmentPrefill]);

  useEffect(() => {
    if (!hasApartmentPrefill) {
      return;
    }

    setDocumentKind("WEEKLY_APARTMENT");
  }, [hasApartmentPrefill]);

  useEffect(() => {
    if (!hasPublicAreaPrefill || !publicAreaPrefill.publicAreaId) {
      return;
    }

    setDocumentKind("WEEKLY_PUBLIC_AREA");
    setPublicAreaId(publicAreaPrefill.publicAreaId as PublicAreaId);
  }, [hasPublicAreaPrefill, publicAreaPrefill.publicAreaId]);

  useEffect(() => {
    if (!hasApartmentPrefill || apartmentSelection || !projectId) {
      return;
    }

    let cancelled = false;

    startTransition(() => {
      void (async () => {
        let apartments = offlineApartments;
        if (canCallVisitReportApi) {
          try {
            apartments = await listProjectApartments(projectId);
          } catch {
            apartments = offlineApartments;
          }
        }

        if (cancelled) {
          return;
        }

        const selection = resolveApartmentSelectionFromPrefill(
          apartments,
          apartmentPrefill
        );
        if (selection) {
          setApartmentSelection(selection);
        }
      })();
    });

    return () => {
      cancelled = true;
    };
  }, [
    apartmentPrefill,
    apartmentSelection,
    canCallVisitReportApi,
    hasApartmentPrefill,
    offlineApartments,
    projectId,
  ]);

  const canSubmit =
    Boolean(catalog)
    && isWeeklyDocumentWizardKind(documentKind)
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
      || !isWeeklyDocumentWizardKind(documentKind)
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
        documentType: documentTypeFromWizardKind(documentKind),
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

  function handleConfirmCancel() {
    setCancelDialogOpen(false);
    router.push(`/projects/${encodeURIComponent(projectId)}`);
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
          בחר סוג מסמך, יחידה ושלב בנייה — ואז התחל את הצ&apos;קליסט.
        </p>
        {hasApartmentPrefill && apartmentSelection ? (
          <p className="rounded-xl bg-sky-50 px-4 py-3 text-sm text-sky-900 dark:bg-sky-950/40 dark:text-sky-200">
            דירה {apartmentSelection.apartmentNumber} נבחרה מהדשבורד — השלימו
            שלב בנייה והתחילו את הביקור.
          </p>
        ) : null}
        {hasPublicAreaPrefill && publicAreaId ? (
          <p className="rounded-xl bg-sky-50 px-4 py-3 text-sm text-sky-900 dark:bg-sky-950/40 dark:text-sky-200">
            אזור ציבורי נבחר מהדשבורד — השלימו שלב בנייה והתחילו את הביקור.
          </p>
        ) : null}
        <p className="text-xs text-zinc-500">
          {fieldReportDataSourceModeLabelHe(dataSourceMode)}
          {pinging ? " · בודק חיבור..." : ""}
        </p>
      </header>

      <form onSubmit={(event) => void handleSubmit(event)} className="space-y-6">
        <DocumentKindPicker value={documentKind} onChange={setDocumentKind} />

        {documentKind === "WEEKLY_APARTMENT"
        && !(hasApartmentPrefill && apartmentSelection) ? (
          <ApartmentPicker
            projectId={projectId}
            value={apartmentSelection}
            onChange={setApartmentSelection}
            canLoadFromApi={canCallVisitReportApi}
            offlineApartments={offlineApartments}
          />
        ) : null}

        {documentKind === "WEEKLY_PUBLIC_AREA" ? (
          <PublicAreaPicker value={publicAreaId} onChange={setPublicAreaId} />
        ) : null}

        {isWeeklyDocumentWizardKind(documentKind) ? (
          <ConstructionStagePicker
            value={constructionStage}
            onChange={setConstructionStage}
          />
        ) : null}

        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        {notice ? (
          <p className="text-sm text-amber-700 dark:text-amber-300">{notice}</p>
        ) : null}

        <div className="flex flex-wrap gap-3">
          <Button type="submit" disabled={submitting || !canSubmit}>
            {submitting ? "יוצר..." : "התחל ביקור"}
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
