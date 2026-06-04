"use client";

import { FileUp, Upload } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import Button from "@/components/ui/Button";
import { apiFetch } from "@/lib/api/client";
import { showToast } from "@/lib/ui/toast";

type Project = {
  id: string;
  project_name: string;
};

export default function UploadPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    async function loadProjects() {
      try {
        const response = await apiFetch("/projects");
        const data = await response.json();
        setProjects(data);
      } catch (error) {
        console.error(error);
      }
    }

    void loadProjects();
  }, []);

  function handleFileSelected(file: File | undefined) {
    if (!file) {
      return;
    }

    setSelectedFile(file);
  }

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    handleFileSelected(event.target.files?.[0]);
    event.target.value = "";
  }

  function openFilePicker() {
    fileInputRef.current?.click();
  }

  async function uploadReport() {
    if (!selectedProject || !selectedFile) {
      return;
    }

    try {
      setUploading(true);

      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("project_id", selectedProject);

      const response = await apiFetch("/reports/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      showToast("הדוח הועלה בהצלחה", "success");
      setSelectedFile(null);
    } catch (error) {
      console.error(error);
      showToast("שגיאה בהעלאת הדוח", "error");
    } finally {
      setUploading(false);
    }
  }

  const canSubmit = Boolean(selectedProject && selectedFile && !uploading);

  return (
    <main className="of-dashboard-page">
      <div className="mx-auto max-w-3xl">
        <div className="mb-10">
          <h1 className="of-page-title">העלאת דוח שבועי</h1>
          <p className="of-page-desc mt-4">
            העלאת דוחות לצורך ניתוח AI תפעולי
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
              className="w-full rounded-2xl border border-zinc-300 bg-white px-4 py-4 dark:border-zinc-700 dark:bg-zinc-950"
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
            <p className="mb-3 font-semibold">שלב 1 — בחירת מסמך</p>

            <div
              role="button"
              tabIndex={0}
              aria-label="אזור העלאת קובץ — לחץ או גרור קובץ"
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  openFilePicker();
                }
              }}
              onClick={openFilePicker}
              onDragOver={(event) => {
                event.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragOver(false);
                handleFileSelected(event.dataTransfer.files?.[0]);
              }}
              className={`
                flex
                w-full
                cursor-pointer
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
                  dragOver
                    ? "border-brand bg-brand/10 shadow-inner dark:border-brand-light"
                    : selectedFile
                      ? "border-emerald-400/80 bg-emerald-50/60 dark:border-emerald-600/60 dark:bg-emerald-950/30"
                      : "border-zinc-300 hover:border-brand/60 hover:bg-brand/5 dark:border-zinc-600 dark:hover:border-brand-light/50"
                }
              `}
            >
              <input
                ref={fileInputRef}
                id="weekly-report-file"
                type="file"
                accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.png,.jpg,.jpeg"
                className="hidden"
                onChange={handleFileChange}
              />

              <span
                className={`
                  flex
                  h-16
                  w-16
                  items-center
                  justify-center
                  rounded-2xl
                  ${
                    selectedFile
                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300"
                      : "bg-brand/15 text-brand dark:bg-brand/25 dark:text-brand-light"
                  }
                `}
              >
                {selectedFile ? (
                  <FileUp className="h-8 w-8" aria-hidden />
                ) : (
                  <Upload className="h-8 w-8" aria-hidden />
                )}
              </span>

              <div className="flex w-full max-w-md flex-col items-center gap-2">
                <p className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  {selectedFile ? "קובץ נבחר" : "גרור קובץ לכאן"}
                </p>
                <p className="text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
                  {selectedFile
                    ? "לחץ כדי להחליף את הקובץ"
                    : "או לחץ באזור זה לבחירת מסמך מהמחשב"}
                </p>
                <p className="text-xs text-zinc-500">
                  PDF · Word · Excel · CSV · תמונות
                </p>
              </div>

              {selectedFile ? (
                <p className="max-w-full truncate rounded-xl bg-white/80 px-4 py-2 text-sm font-medium text-zinc-800 dark:bg-zinc-950/80 dark:text-zinc-200">
                  {selectedFile.name}
                </p>
              ) : null}
            </div>
          </div>

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
              {selectedFile ? "החלף קובץ" : "העלאת קובץ"}
            </Button>

            <Button
              variant="primary"
              size="lg"
              onClick={() => void uploadReport()}
              disabled={!canSubmit}
              className="w-full justify-center py-4 text-lg"
            >
              {uploading ? "מעלה דוח..." : "העלאת הדוח ל-AI"}
            </Button>

            {!selectedProject ? (
              <p className="text-center text-xs text-zinc-500">
                יש לבחור פרויקט לפני שליחה ל-AI
              </p>
            ) : null}
            {selectedProject && !selectedFile ? (
              <p className="text-center text-xs text-zinc-500">
                יש לבחור קובץ לפני שליחה ל-AI
              </p>
            ) : null}
          </div>
        </div>
      </div>
    </main>
  );
}
