"use client";

import Link from "next/link";
import { useCallback, useState } from "react";

import Badge from "@/components/ui/Badge";
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
import { useAuth } from "@/contexts/AuthContext";
import { useAsyncData } from "@/hooks/useAsyncData";
import { useFiltering } from "@/hooks/useFiltering";
import { usePagination } from "@/hooks/usePagination";
import { useSorting } from "@/hooks/useSorting";
import { apiFetch } from "@/lib/api/client";
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

function displayStakeholder(
  value?: string | null
) {
  const trimmed = value?.trim();
  return trimmed || "לא צוין";
}

type ProjectSortKey = "project_name" | "created_at" | "status";

export default function ProjectsPage() {
  const { t } = useI18n();
  const { isOnline } = useOffline();
  const { profile, currentOrgId } = useAuth();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newProject, setNewProject] = useState({
    project_name: "",
    developer_name: "",
    contractor_name: "",
    lawyer_name: "",
    supervisor_name: "",
    supervisor_email: "",
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
      !newProject.supervisor_name.trim()
    ) {
      showToast(
        "יש למלא את כל שדות החובה: שם פרויקט, יזם, קבלן, עו״ד מלווה ומפקח מלווה",
        "error"
      );
      return;
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
          organization_id: currentOrgId || profile?.organization_id || null,
          owner_id: profile?.id || null,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to create project");
      }

      setNewProject({
        project_name: "",
        developer_name: "",
        contractor_name: "",
        lawyer_name: "",
        supervisor_name: "",
        supervisor_email: "",
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

  function getStatusLabel(status: string) {
    switch (status) {
      case "ACTIVE":
        return "פעיל";
      case "COMPLETED":
        return "הושלם";
      default:
        return status;
    }
  }

  return (
    <PageShell
      title={t("projects.title")}
      description="ניהול פרויקטים הנדסיים במערכת"
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
            <Card key={project.id}>
              <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h2 className="text-2xl font-semibold">
                    <Link
                      href={`/projects/${project.id}`}
                      className="hover:underline"
                    >
                      {project.project_name}
                    </Link>
                  </h2>
                  <p className="mt-2 text-zinc-500">
                    יזם: {displayStakeholder(project.developer_name)}
                    {" · "}
                    קבלן: {displayStakeholder(project.contractor_name)}
                  </p>
                </div>

                <Badge variant="success">
                  {getStatusLabel(project.status)}
                </Badge>
              </div>

              <div className="space-y-4">
                <div>
                  <h3 className="mb-2 font-semibold">
                    עו״ד מלווה
                  </h3>
                  <p>{displayStakeholder(project.lawyer_name)}</p>
                </div>

                <div>
                  <h3 className="mb-2 font-semibold">
                    מפקח מלווה
                  </h3>
                  <p>{project.supervisor_name}</p>
                </div>

                <div>
                  <h3 className="mb-2 font-semibold">
                    אימייל מפקח מלווה
                  </h3>
                  <p>{project.supervisor_email || "-"}</p>
                </div>

                <div>
                  <h3 className="mb-2 font-semibold">
                    תאריך יצירה
                  </h3>
                  <p>
                    {new Date(
                      project.created_at
                    ).toLocaleDateString("he-IL")}
                  </p>
                </div>
              </div>
            </Card>
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
