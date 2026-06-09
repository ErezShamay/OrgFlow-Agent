"use client";

import {
  CheckCircle2,
  Clock,
  FileUp,
  Loader2,
  Upload,
  X,
  XCircle,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

import Button from "@/components/ui/Button";
import { apiFetch } from "@/lib/api/client";
import {
  normalizeProjectList,
  readApiErrorMessage,
} from "@/lib/api/read-error-message";
import { showToast } from "@/lib/ui/toast";

type Project = {
  id: string;
  project_name: string;
};

type UploadFileStatus = "pending" | "uploading" | "success" | "error";

type UploadQueueItem = {
  id: string;
  file: File;
  status: UploadFileStatus;
  errorMessage?: string;
};

type BulkUploadJob = {
  job_id: string;
  project_id: string;
  total_files: number;
  processed_files: number;
  successful_uploads: number;
  failed_uploads: number;
  progress_percent: number;
  status: "IN_PROGRESS" | "COMPLETED" | string;
  results?: Array<{
    success?: boolean;
    filename?: string;
    error_message?: string;
    error_code?: string;
  }>;
};

const ACCEPTED_EXTENSIONS =
  ".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.png,.jpg,.jpeg";

const POLL_INTERVAL_MS = 600;
const MAX_POLL_ATTEMPTS = 600;

function fileQueueId(file: File): string {
  return `${file.name}-${file.size}-${file.lastModified}`;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function statusLabel(status: UploadFileStatus): string {
  switch (status) {
    case "pending":
      return "ממתין";
    case "uploading":
      return "מעלה ומעבד";
    case "success":
      return "הושלם";
    case "error":
      return "נכשל";
  }
}

function resultErrorMessage(
  result: NonNullable<BulkUploadJob["results"]>[number]
): string {
  if (result.error_message?.trim()) {
    return result.error_message;
  }
  if (result.error_code === "UNSUPPORTED_FILE_TYPE") {
    return "סוג הקובץ אינו נתמך";
  }
  return "שגיאה בהעלאת הדוח";
}

function StatusIcon({ status }: { status: UploadFileStatus }) {
  switch (status) {
    case "pending":
      return <Clock className="h-5 w-5 text-zinc-400" aria-hidden />;
    case "uploading":
      return (
        <Loader2
          className="h-5 w-5 animate-spin text-brand"
          aria-hidden
        />
      );
    case "success":
      return (
        <CheckCircle2
          className="h-5 w-5 text-emerald-600 dark:text-emerald-400"
          aria-hidden
        />
      );
    case "error":
      return (
        <XCircle
          className="h-5 w-5 text-red-600 dark:text-red-400"
          aria-hidden
        />
      );
  }
}

export default function UploadPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState("");
  const [queue, setQueue] = useState<UploadQueueItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    async function loadProjects() {
      try {
        const response = await apiFetch("/projects");
        if (!response.ok) {
          throw new Error("Failed to load projects");
        }

        const data = await response.json();
        setProjects(normalizeProjectList(data));
      } catch (error) {
        console.error(error);
        showToast("שגיאה בטעינת רשימת הפרויקטים", "error");
      }
    }

    void loadProjects();
  }, []);

  function addFiles(files: FileList | File[] | null | undefined) {
    const selected = Array.from(files ?? []);
    if (selected.length === 0) {
      return;
    }

    setQueue((current) => {
      const existingIds = new Set(current.map((item) => item.id));
      const next = [...current];

      for (const file of selected) {
        const id = fileQueueId(file);
        if (existingIds.has(id)) {
          continue;
        }
        existingIds.add(id);
        next.push({ id, file, status: "pending" });
      }

      return next;
    });
  }

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    addFiles(event.target.files);
    event.target.value = "";
  }

  function removeFile(id: string) {
    if (uploading) {
      return;
    }
    setQueue((current) => current.filter((item) => item.id !== id));
  }

  function clearCompleted() {
    if (uploading) {
      return;
    }
    setQueue((current) =>
      current.filter((item) => item.status !== "success")
    );
  }

  function openFilePicker() {
    fileInputRef.current?.click();
  }

  function updateQueueItem(
    id: string,
    patch: Partial<Pick<UploadQueueItem, "status" | "errorMessage">>
  ) {
    setQueue((current) =>
      current.map((item) =>
        item.id === id ? { ...item, ...patch } : item
      )
    );
  }

  function applyJobProgress(
    job: BulkUploadJob,
    pendingItems: UploadQueueItem[]
  ) {
    const results = job.results ?? [];

    for (let index = 0; index < pendingItems.length; index += 1) {
      const item = pendingItems[index];
      const result = results[index];

      if (!result) {
        if (job.status === "IN_PROGRESS") {
          updateQueueItem(item.id, {
            status: "uploading",
            errorMessage: undefined,
          });
        }
        continue;
      }

      updateQueueItem(item.id, {
        status: result.success ? "success" : "error",
        errorMessage: result.success ? undefined : resultErrorMessage(result),
      });
    }
  }

  async function pollBulkJob(
    projectId: string,
    jobId: string,
    pendingItems: UploadQueueItem[]
  ): Promise<BulkUploadJob> {
    for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt += 1) {
      const response = await apiFetch(
        `/projects/${projectId}/reports/upload-jobs/${jobId}`
      );

      if (!response.ok) {
        const message = await readApiErrorMessage(
          response,
          "שגיאה בבדיקת סטטוס ההעלאה"
        );
        throw new Error(message);
      }

      const job = (await response.json()) as BulkUploadJob;
      applyJobProgress(job, pendingItems);

      if (job.status === "COMPLETED") {
        return job;
      }

      await sleep(POLL_INTERVAL_MS);
    }

    throw new Error("העלאת הדוחות נמשכה זמן רב מדי");
  }

  async function uploadReports() {
    if (!selectedProject || queue.length === 0 || uploading) {
      return;
    }

    const pendingItems = queue.filter(
      (item) => item.status === "pending" || item.status === "error"
    );

    if (pendingItems.length === 0) {
      showToast("כל הקבצים כבר הועלו", "info");
      return;
    }

    setUploading(true);

    for (const item of pendingItems) {
      updateQueueItem(item.id, {
        status: "uploading",
        errorMessage: undefined,
      });
    }

    const formData = new FormData();
    formData.append("project_id", selectedProject);
    for (const item of pendingItems) {
      formData.append("files", item.file);
    }

    try {
      const response = await apiFetch("/reports/upload/bulk", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const message = await readApiErrorMessage(
          response,
          "שגיאה בהעלאת הדוחות"
        );
        for (const item of pendingItems) {
          updateQueueItem(item.id, {
            status: "error",
            errorMessage: message,
          });
        }
        showToast(message, "error");
        return;
      }

      const initialJob = (await response.json()) as BulkUploadJob;
      const finalJob =
        initialJob.status === "COMPLETED"
          ? initialJob
          : await pollBulkJob(
              selectedProject,
              initialJob.job_id,
              pendingItems
            );

      applyJobProgress(finalJob, pendingItems);

      const successCount = finalJob.successful_uploads ?? 0;
      const failureCount = finalJob.failed_uploads ?? 0;

      if (failureCount === 0) {
        showToast(
          `הועלו בהצלחה ${successCount} דוחות — הם יופיעו בארכיון מסמכי הפרויקט`,
          "success"
        );
      } else if (successCount === 0) {
        showToast("כל ההעלאות נכשלו", "error");
      } else {
        showToast(
          `הועלו ${successCount} דוחות, ${failureCount} נכשלו`,
          "info"
        );
      }
    } catch (error) {
      console.error(error);
      const message =
        error instanceof Error ? error.message : "שגיאה בהעלאת הדוחות";
      for (const item of pendingItems) {
        updateQueueItem(item.id, {
          status: "error",
          errorMessage: message,
        });
      }
      showToast(message, "error");
    } finally {
      setUploading(false);
    }
  }

  const pendingCount = queue.filter((item) => item.status === "pending").length;
  const uploadingCount = queue.filter(
    (item) => item.status === "uploading"
  ).length;
  const successCount = queue.filter((item) => item.status === "success").length;
  const errorCount = queue.filter((item) => item.status === "error").length;
  const completedCount = successCount + errorCount;
  const overallProgress =
    queue.length > 0 ? Math.round((completedCount / queue.length) * 100) : 0;
  const hasPendingWork =
    pendingCount > 0 || errorCount > 0 || uploadingCount > 0;
  const canSubmit = Boolean(
    selectedProject && queue.length > 0 && hasPendingWork && !uploading
  );

  return (
    <main className="of-dashboard-page">
      <div className="mx-auto max-w-3xl">
        <div className="mb-10">
          <h1 className="of-page-title">העלאת דוח שבועי</h1>
          <p className="of-page-desc mt-4">
            העלאת דוחות לצורך ניתוח AI תפעולי — ניתן לבחור מספר קבצים בבת אחת
          </p>
        </div>

        <div className="of-card of-card-p8 shadow-sm">
          <div className="mb-8">
            <label
              htmlFor="upload-project"
              className="mb-3 block font-semibold"
            >
              בחירת פרויקט
            </label>
            <select
              id="upload-project"
              value={selectedProject}
              onChange={(event) => setSelectedProject(event.target.value)}
              disabled={uploading}
              className="w-full rounded-2xl border border-zinc-300 bg-white px-4 py-4 disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-950"
            >
              <option value="">בחר פרויקט</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.project_name}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-8">
            <p className="mb-3 font-semibold">שלב 1 — בחירת מסמכים</p>

            <input
              ref={fileInputRef}
              id="weekly-report-file"
              type="file"
              accept={ACCEPTED_EXTENSIONS}
              multiple
              className="sr-only"
              disabled={uploading}
              onChange={handleFileChange}
            />

            <label
              htmlFor={uploading ? undefined : "weekly-report-file"}
              aria-label="אזור העלאת קבצים — לחץ או גרור קבצים"
              onDragOver={(event) => {
                event.preventDefault();
                if (!uploading) {
                  setDragOver(true);
                }
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragOver(false);
                if (!uploading) {
                  addFiles(event.dataTransfer.files);
                }
              }}
              className={`
                flex
                w-full
                flex-col
                items-center
                justify-center
                gap-3
                rounded-3xl
                border-2
                border-dashed
                bg-zinc-50/90
                px-6
                py-12
                text-center
                transition-all
                dark:bg-zinc-900/50
                ${
                  uploading
                    ? "cursor-not-allowed opacity-70"
                    : "cursor-pointer"
                }
                ${
                  dragOver
                    ? "border-brand bg-brand/10 shadow-inner dark:border-brand-light"
                    : queue.length > 0
                      ? "border-emerald-400/80 bg-emerald-50/60 dark:border-emerald-600/60 dark:bg-emerald-950/30"
                      : "border-zinc-300 hover:border-brand/60 hover:bg-brand/5 dark:border-zinc-600 dark:hover:border-brand-light/50"
                }
              `}
            >
              <span
                className={`
                  flex
                  h-16
                  w-16
                  items-center
                  justify-center
                  rounded-2xl
                  ${
                    queue.length > 0
                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300"
                      : "bg-brand/15 text-brand dark:bg-brand/25 dark:text-brand-light"
                  }
                `}
              >
                {queue.length > 0 ? (
                  <FileUp className="h-8 w-8" aria-hidden />
                ) : (
                  <Upload className="h-8 w-8" aria-hidden />
                )}
              </span>

              <div className="flex w-full max-w-md flex-col items-center gap-2">
                <p className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  {queue.length > 0
                    ? `${queue.length} קבצים נבחרו`
                    : "גרור קבצים לכאן"}
                </p>
                <p className="text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
                  {queue.length > 0
                    ? "לחץ כדי להוסיף עוד קבצים"
                    : "או לחץ באזור זה לבחירת מסמכים מהמחשב"}
                </p>
                <p className="text-xs text-zinc-500">
                  PDF · Word · Excel · CSV · תמונות
                </p>
                <p className="text-xs text-zinc-500">
                  לבחירת מספר קבצים: החזק Cmd (Mac) או Ctrl (Windows)
                </p>
              </div>
            </label>
          </div>

          {queue.length > 0 ? (
            <div className="mb-8">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <p className="font-semibold">סטטוס קבצים</p>
                <div className="flex flex-wrap gap-2 text-xs text-zinc-500">
                  {pendingCount > 0 ? <span>{pendingCount} ממתינים</span> : null}
                  {uploadingCount > 0 ? (
                    <span>{uploadingCount} בעיבוד</span>
                  ) : null}
                  {successCount > 0 ? (
                    <span className="text-emerald-600 dark:text-emerald-400">
                      {successCount} הושלמו
                    </span>
                  ) : null}
                  {errorCount > 0 ? (
                    <span className="text-red-600 dark:text-red-400">
                      {errorCount} נכשלו
                    </span>
                  ) : null}
                </div>
              </div>

              {(uploading || completedCount > 0) && (
                <div className="mb-4">
                  <div className="mb-2 flex items-center justify-between text-sm text-zinc-600 dark:text-zinc-400">
                    <span>התקדמות כללית</span>
                    <span>{overallProgress}%</span>
                  </div>
                  <div
                    className="h-2 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800"
                    role="progressbar"
                    aria-valuenow={overallProgress}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label="התקדמות העלאה"
                  >
                    <div
                      className="h-full rounded-full bg-brand transition-all duration-300"
                      style={{ width: `${overallProgress}%` }}
                    />
                  </div>
                </div>
              )}

              <ul
                className="max-h-80 space-y-2 overflow-y-auto rounded-2xl border border-zinc-200 p-3 dark:border-zinc-800"
                aria-live="polite"
                aria-relevant="additions text"
              >
                {queue.map((item) => (
                  <li
                    key={item.id}
                    className={`
                      flex
                      items-start
                      gap-3
                      rounded-xl
                      px-3
                      py-3
                      ${
                        item.status === "success"
                          ? "bg-emerald-50/80 dark:bg-emerald-950/20"
                          : item.status === "error"
                            ? "bg-red-50/80 dark:bg-red-950/20"
                            : item.status === "uploading"
                              ? "bg-brand/5 dark:bg-brand/10"
                              : "bg-zinc-50 dark:bg-zinc-900/50"
                      }
                    `}
                  >
                    <StatusIcon status={item.status} />

                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-100">
                        {item.file.name}
                      </p>
                      <p className="mt-0.5 text-xs text-zinc-500">
                        {formatFileSize(item.file.size)} · {statusLabel(item.status)}
                      </p>
                      {item.errorMessage ? (
                        <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                          {item.errorMessage}
                        </p>
                      ) : null}
                    </div>

                    {!uploading &&
                    (item.status === "pending" || item.status === "error") ? (
                      <button
                        type="button"
                        onClick={() => removeFile(item.id)}
                        className="rounded-lg p-1 text-zinc-400 transition-colors hover:bg-zinc-200 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-200"
                        aria-label={`הסר ${item.file.name}`}
                      >
                        <X className="h-4 w-4" />
                      </button>
                    ) : null}
                  </li>
                ))}
              </ul>

              {successCount > 0 && !uploading ? (
                <button
                  type="button"
                  onClick={clearCompleted}
                  className="mt-3 text-sm text-zinc-500 underline-offset-2 hover:text-zinc-700 hover:underline dark:hover:text-zinc-300"
                >
                  נקה קבצים שהושלמו
                </button>
              ) : null}
            </div>
          ) : null}

          <div className="flex flex-col gap-3 border-t border-zinc-200 pt-8 dark:border-zinc-800">
            <p className="font-semibold">שלב 2 — שליחה לניתוח</p>

            <Button
              type="button"
              variant="secondary"
              size="lg"
              disabled={uploading}
              onClick={openFilePicker}
              className="w-full justify-center py-4 text-base"
            >
              {queue.length > 0 ? "הוסף קבצים" : "בחר קבצים"}
            </Button>

            <Button
              variant="primary"
              size="lg"
              onClick={() => void uploadReports()}
              disabled={!canSubmit}
              className="w-full justify-center py-4 text-lg"
            >
              {uploading
                ? `מעלה דוחות (${completedCount}/${queue.length})...`
                : queue.length > 1
                  ? `העלאת ${pendingCount || queue.length} דוחות ל-AI`
                  : "העלאת הדוח ל-AI"}
            </Button>

            {!selectedProject ? (
              <p className="text-center text-xs text-zinc-500">
                יש לבחור פרויקט לפני שליחה ל-AI
              </p>
            ) : null}
            {selectedProject && queue.length === 0 ? (
              <p className="text-center text-xs text-zinc-500">
                יש לבחור לפחות קובץ אחד לפני שליחה ל-AI
              </p>
            ) : null}
          </div>
        </div>
      </div>
    </main>
  );
}
