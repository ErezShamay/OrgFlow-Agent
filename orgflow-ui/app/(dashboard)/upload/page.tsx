"use client";

import {
  useEffect,
  useState,
} from "react";

import Button from "@/components/ui/Button";
import { apiFetch } from "@/lib/api/client";
import { showToast } from "@/lib/ui/toast";

type Project = {
  id: string;
  project_name: string;
};

export default function UploadPage() {

  const [projects, setProjects] =
    useState<Project[]>([]);

  const [selectedProject, setSelectedProject] =
    useState("");

  const [selectedFile, setSelectedFile] =
    useState<File | null>(null);

  const [uploading, setUploading] =
    useState(false);

  // =========================
  // LOAD PROJECTS
  // =========================

  useEffect(() => {

    async function loadProjects() {

      try {

        const response =
          await apiFetch("/projects");

        const data =
          await response.json();

        setProjects(data);

      } catch (error) {

        console.error(error);
      }
    }

    loadProjects();

  }, []);

  // =========================
  // FILE CHANGE
  // =========================

  function handleFileChange(
    event: React.ChangeEvent<HTMLInputElement>
  ) {

    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    setSelectedFile(file);
  }

  // =========================
  // UPLOAD
  // =========================

  async function uploadReport() {

    if (
      !selectedProject ||
      !selectedFile
    ) {
      return;
    }

    try {

      setUploading(true);

      const formData =
        new FormData();

      formData.append(
        "file",
        selectedFile
      );

      formData.append(
        "project_id",
        selectedProject
      );

      const response =
        await apiFetch(
          "/reports/upload",
          {
            method: "POST",
            body: formData,
          }
        );

      if (!response.ok) {
        throw new Error(
          "Upload failed"
        );
      }

      showToast(
        "הדוח הועלה בהצלחה",
        "success"
      );

      setSelectedFile(null);

    } catch (error) {

      console.error(error);

      showToast(
        "שגיאה בהעלאת הדוח",
        "error"
      );

    } finally {

      setUploading(false);
    }
  }

  return (

    <main className="of-dashboard-page">

      <div className="mx-auto max-w-3xl">

        {/* HEADER */}

        <div className="mb-10">

          <h1 className="of-page-title">
            העלאת דוח שבועי
          </h1>

          <p className="of-page-desc mt-4">
            העלאת דוחות לצורך ניתוח AI תפעולי
          </p>

        </div>

        {/* CARD */}

        <div className="of-card of-card-p8 shadow-sm">

          {/* PROJECT SELECT */}

          <div className="mb-8">

            <label
              className="
                block
                mb-3
                font-semibold
              "
            >
              בחירת פרויקט
            </label>

            <select
              value={selectedProject}

              onChange={(event) =>
                setSelectedProject(
                  event.target.value
                )
              }

              className="
                w-full
                rounded-2xl
                border
                border-zinc-300
                dark:border-zinc-700
                bg-white
                dark:bg-zinc-950
                px-4
                py-4
              "
            >

              <option value="">
                בחר פרויקט
              </option>

              {projects.map((project) => (

                <option
                  key={project.id}
                  value={project.id}
                >
                  {project.project_name}
                </option>

              ))}

            </select>

          </div>

          {/* FILE UPLOAD */}

          <div className="mb-8">

            <label
              className="
                block
                mb-3
                font-semibold
              "
            >
              העלאת קובץ
            </label>

            <div
              className="
                border-2
                border-dashed
                border-zinc-300
                dark:border-zinc-700
                rounded-3xl
                p-10
                text-center
              "
            >

              <input
                type="file"

                onChange={
                  handleFileChange
                }

                className="mb-4"
              />

              <p
                className="
                  text-zinc-500
                "
              >
                PDF / DOCX / Images
              </p>

              {selectedFile && (

                <div
                  className="
                    mt-6
                    text-sm
                    font-medium
                  "
                >
                  {selectedFile.name}
                </div>

              )}

            </div>

          </div>

          {/* ACTION */}

          <Button
            variant="primary"
            size="lg"
            onClick={uploadReport}
            disabled={
              uploading ||
              !selectedProject ||
              !selectedFile
            }
            className="w-full justify-center py-4 text-lg"
          >

            {uploading
              ? "מעלה דוח..."
              : "העלאת דוח ל-AI"}

          </Button>

        </div>

      </div>

    </main>
  );
}