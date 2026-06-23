"use client";

import { useCallback, useMemo, useState } from "react";

import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import EmptyState from "@/components/ui/EmptyState";
import FilterBar from "@/components/ui/FilterBar";
import LoadingState from "@/components/ui/LoadingState";
import PageLoadingOverlay from "@/components/ui/PageLoadingOverlay";
import PageShell from "@/components/ui/PageShell";
import PaginationControls from "@/components/ui/Pagination";
import RetryPanel from "@/components/ui/RetryPanel";
import SortSelect from "@/components/ui/SortSelect";
import ProjectOverviewListCard from "@/components/projects/ProjectOverviewListCard";
import ProjectSchemeSelect from "@/components/projects/ProjectSchemeSelect";
import { useAuth } from "@/contexts/AuthContext";
import { useAsyncData } from "@/hooks/useAsyncData";
import { useEffectiveRole } from "@/hooks/useEffectiveRole";
import { useOrgQuery } from "@/hooks/useOrgQuery";
import { useFiltering } from "@/hooks/useFiltering";
import { usePagination } from "@/hooks/usePagination";
import { useSorting } from "@/hooks/useSorting";
import { apiFetch } from "@/lib/api/client";
import type { ProjectScheme } from "@/lib/field-reports/schema/types";
import {
  canViewProjectSupervisionDashboard,
  fetchProjectSupervisionSummaries,
} from "@/lib/projects/supervision-dashboard";
import type { SupervisionOverallStatus } from "@/lib/projects/supervision-dashboard-types";
import { showToast } from "@/lib/ui/toast";
import { useI18n } from "@/providers/I18nProvider";
import { useOffline } from "@/providers/OfflineProvider";

type Project = {
  id: string;
  project_name: string;
  developer_name?: string | null;
  contractor_name?: string | null;
  lawyer_name?: string | null;
  supervisor_name: string;
  supervisor_email: string;
  status: string;
  created_at: string;
};

type ProjectSortKey = "project_name" | "created_at" | "status";

export default function ProjectsPage() {
  const { t } = useI18n();
  const { isOnline } = useOffline();
  const { profile, currentOrgId } = useAuth();
  const effectiveRole = useEffectiveRole();
  const canLoadSupervisionSummaries =
    canViewProjectSupervisionDashboard(effectiveRole);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [expandedProjectIds, setExpandedProjectIds] = useState<
    ReadonlySet<string>
  >(() => new Set());
  const [newProject, setNewProject] = useState({
    project_name: "",
    developer_name: "",
    contractor_name: "",
    lawyer_name: "",
    supervisor_name: "",
    supervisor_email: "",
    scheme: "" as ProjectScheme | "",
    housing_units_count: "",
    floors_count: "",
  });

  const loadProjects = useCallback(async () => {
    if (!isOnline) {
      throw new Error(t("common.offline"));
    }

    const response = await apiFetch("/projects");

    if (!response.ok) {
      throw new Error("Failed to load projects");
    }

    return (await response.json()) as Project[];
  }, [isOnline, t]);

  const {
    data: projects,
    loading,
    isValidating,
    error,
    retry,
  } = useAsyncData(loadProjects, {
    cacheKey: "projects",
    showErrorToast: true,
    errorMessage: t("common.error"),
  });

  const projectList = projects ?? [];

  const loadSupervisionSummaries = useCallback(async () => {
    return fetchProjectSupervisionSummaries();
  }, []);

  const { data: supervisionSummaries } = useOrgQuery(
    "projects/supervision-summaries",
    loadSupervisionSummaries,
    {
      enabled: canLoadSupervisionSummaries && Boolean(projects?.length),
      showErrorToast: false,
    }
  );

  const supervisionStatusByProjectId = useMemo(() => {
    const map = new Map<string, SupervisionOverallStatus>();
    for (const item of supervisionSummaries?.items ?? []) {
      map.set(item.project_id, item.overall_status);
    }
    return map;
  }, [supervisionSummaries?.items]);

  const { filteredItems, searchQuery, setSearchQuery } =
    useFiltering<Project, "project_name">(
      projectList,
      (item, field) => item[field],
      "project_name"
    );

  const { sortedItems, sortKey, direction, setSort, options } =
    useSorting<Project, ProjectSortKey>(
      filteredItems,
      [
        { key: "project_name", label: "שם פרויקט" },
        { key: "created_at", label: "תאריך" },
        { key: "status", label: "סטטוס" },
      ],
      (item, key) => {
        if (key === "created_at") {
          return new Date(item.created_at).getTime();
        }

        return item[key];
      },
      "project_name"
    );

  const pagination = usePagination(sortedItems, 6);

  async function handleCreateProject(event: React.FormEvent) {
    event.preventDefault();

    if (
      !newProject.project_name.trim() ||
      !newProject.developer_name.trim() ||
      !newProject.contractor_name.trim() ||
      !newProject.lawyer_name.trim() ||
      !newProject.supervisor_name.trim() ||
      !newProject.scheme
    ) {
      showToast(
        "יש למלא את כל שדות החובה: שם פרויקט, סוג פרויקט, יזם, קבלן, עו״ד מלווה ומפקח מלווה",
        "error"
      );
      return;
    }

    const housingUnitsRaw = newProject.housing_units_count.trim();
    let housing_units_count: number | undefined;
    if (housingUnitsRaw) {
      const parsed = Number(housingUnitsRaw);
      if (!Number.isInteger(parsed) || parsed < 1) {
        showToast("מספר יחידות דיור חייב להיות מספר שלם חיובי", "error");
        return;
      }
      housing_units_count = parsed;
    }

    const floorsRaw = newProject.floors_count.trim();
    let floors_count: number | undefined;
    if (floorsRaw) {
      const parsed = Number(floorsRaw);
      if (!Number.isInteger(parsed) || parsed < 1) {
        showToast("מספר קומות חייב להיות מספר שלם חיובי", "error");
        return;
      }
      floors_count = parsed;
    }

    try {
      setCreating(true);

      const response = await apiFetch("/projects", {
        method: "POST",
        body: JSON.stringify({
          project_name: newProject.project_name.trim(),
          developer_name: newProject.developer_name.trim(),
          contractor_name: newProject.contractor_name.trim(),
          lawyer_name: newProject.lawyer_name.trim(),
          supervisor_name: newProject.supervisor_name.trim(),
          supervisor_email:
            newProject.supervisor_email.trim() || null,
          scheme: newProject.scheme,
          housing_units_count: housing_units_count ?? null,
          floors_count: floors_count ?? null,
          organization_id: currentOrgId || profile?.organization_id || null,
          owner_id: profile?.id || null,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to create project");
      }

      await response.json();

      setNewProject({
        project_name: "",
        developer_name: "",
        contractor_name: "",
        lawyer_name: "",
        supervisor_name: "",
        supervisor_email: "",
        scheme: "",
        housing_units_count: "",
        floors_count: "",
      });

      showToast("הפרויקט נוצר בהצלחה", "success");
      setShowCreateForm(false);
      await retry();
    } catch {
      showToast("שגיאה ביצירת הפרויקט", "error");
    } finally {
      setCreating(false);
    }
  }

  function toggleProjectExpanded(projectId: string) {
    setExpandedProjectIds((current) => {
      const next = new Set(current);
      if (next.has(projectId)) {
        next.delete(projectId);
      } else {
        next.add(projectId);
      }
      return next;
    });
  }

  return (
    <PageShell
      title={t("projects.title")}
      description="סקירה מרוכזת של כל הפרויקטים — לחצו על «הצג מידע נוסף» לפרטים מלאים"
      actions={
        <Button
          variant="primary"
          size="lg"
          type="button"
          onClick={() => setShowCreateForm(true)}
        >
          יצירת פרויקט חדש
        </Button>
      }
    >
      {showCreateForm ? (
        <Card className="mb-8">
          <div className="mb-6 flex items-center justify-between gap-4">
            <h2 className="text-2xl font-bold">יצירת פרויקט חדש</h2>
            <Button
              variant="secondary"
              type="button"
              onClick={() => setShowCreateForm(false)}
            >
              ביטול
            </Button>
          </div>

          <form
            onSubmit={handleCreateProject}
            className="grid gap-4 md:grid-cols-2"
          >
            <input
              className="rounded-2xl border border-zinc-200 bg-transparent p-4 dark:border-zinc-700"
              placeholder="שם הפרויקט"
              value={newProject.project_name}
              onChange={(event) =>
                setNewProject({
                  ...newProject,
                  project_name: event.target.value,
                })
              }
              required
            />
            <div className="md:col-span-2">
              <label
                htmlFor="new-project-scheme"
                className="mb-2 block text-sm font-medium text-zinc-600 dark:text-zinc-400"
              >
                סוג פרויקט *
              </label>
              <ProjectSchemeSelect
                id="new-project-scheme"
                value={newProject.scheme}
                onChange={(scheme) =>
                  setNewProject({
                    ...newProject,
                    scheme,
                  })
                }
                required
                className="w-full rounded-2xl border border-zinc-200 bg-transparent p-4 dark:border-zinc-700"
              />
            </div>
            <input
              className="rounded-2xl border border-zinc-200 bg-transparent p-4 dark:border-zinc-700"
              placeholder="מספר קומות (אופציונלי)"
              type="number"
              min={1}
              value={newProject.floors_count}
              onChange={(event) =>
                setNewProject({
                  ...newProject,
                  floors_count: event.target.value,
                })
              }
            />
            <input
              className="rounded-2xl border border-zinc-200 bg-transparent p-4 dark:border-zinc-700"
              placeholder="יחידות דיור (אופציונלי)"
              type="number"
              min={1}
              value={newProject.housing_units_count}
              onChange={(event) =>
                setNewProject({
                  ...newProject,
                  housing_units_count: event.target.value,
                })
              }
            />
            <input
              className="rounded-2xl border border-zinc-200 bg-transparent p-4 dark:border-zinc-700"
              placeholder="שם היזם"
              value={newProject.developer_name}
              onChange={(event) =>
                setNewProject({
                  ...newProject,
                  developer_name: event.target.value,
                })
              }
              required
            />
            <input
              className="rounded-2xl border border-zinc-200 bg-transparent p-4 dark:border-zinc-700"
              placeholder="שם הקבלן"
              value={newProject.contractor_name}
              onChange={(event) =>
                setNewProject({
                  ...newProject,
                  contractor_name: event.target.value,
                })
              }
              required
            />
            <input
              className="rounded-2xl border border-zinc-200 bg-transparent p-4 dark:border-zinc-700"
              placeholder="עו״ד מלווה"
              value={newProject.lawyer_name}
              onChange={(event) =>
                setNewProject({
                  ...newProject,
                  lawyer_name: event.target.value,
                })
              }
              required
            />
            <input
              className="rounded-2xl border border-zinc-200 bg-transparent p-4 dark:border-zinc-700"
              placeholder="מפקח מלווה"
              value={newProject.supervisor_name}
              onChange={(event) =>
                setNewProject({
                  ...newProject,
                  supervisor_name: event.target.value,
                })
              }
              required
            />
            <input
              className="rounded-2xl border border-zinc-200 bg-transparent p-4 md:col-span-2 dark:border-zinc-700"
              placeholder="אימייל מפקח מלווה (אופציונלי)"
              type="email"
              value={newProject.supervisor_email}
              onChange={(event) =>
                setNewProject({
                  ...newProject,
                  supervisor_email: event.target.value,
                })
              }
            />
            <Button
              type="submit"
              variant="primary"
              size="lg"
              disabled={creating}
              className="md:col-span-2"
            >
              {creating ? "יוצר פרויקט..." : "צור פרויקט"}
            </Button>
          </form>
        </Card>
      ) : null}

      <div className="mb-6 grid items-end gap-4 md:grid-cols-2">
        <FilterBar
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder={t("common.filter")}
        />
        <SortSelect
          options={options}
          sortKey={sortKey}
          direction={direction}
          onChange={setSort}
        />
      </div>

      {isValidating ? <PageLoadingOverlay /> : null}

      {loading && projectList.length === 0 ? (
        <LoadingState message={t("common.loading")} />
      ) : null}

      {!loading && error ? (
        <RetryPanel
          message={error.message}
          onRetry={() => {
            void retry().catch(() =>
              showToast(t("common.error"), "error")
            );
          }}
        />
      ) : null}

      {!loading && !error && pagination.items.length === 0 ? (
        <EmptyState title={t("projects.empty")} />
      ) : null}

      {!loading && !error ? (
        <div className="grid gap-6">
          {pagination.items.map((project) => (
            <ProjectOverviewListCard
              key={project.id}
              project={project}
              expanded={expandedProjectIds.has(project.id)}
              onToggleExpanded={() => toggleProjectExpanded(project.id)}
              supervisionStatus={
                supervisionStatusByProjectId.get(project.id) ?? null
              }
            />
          ))}
        </div>
      ) : null}

      {!loading && !error ? (
        <PaginationControls
          page={pagination.state.page}
          totalPages={pagination.totalPages}
          pageNumbers={pagination.pageNumbers}
          hasNextPage={pagination.hasNextPage}
          hasPreviousPage={pagination.hasPreviousPage}
          onPageChange={pagination.setPage}
          onNext={pagination.goToNextPage}
          onPrevious={pagination.goToPreviousPage}
        />
      ) : null}
    </PageShell>
  );
}
