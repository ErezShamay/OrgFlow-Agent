"use client";

import {
  useEffect,
  useState,
} from "react";

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
          await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/projects`
          );

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
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/reports/upload`,
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

      alert(
        "הדוח הועלה בהצלחה"
      );

      setSelectedFile(null);

    } catch (error) {

      console.error(error);

      alert(
        "שגיאה בהעלאת הדוח"
      );

    } finally {

      setUploading(false);
    }
  }

  return (

    <main
      className="
        min-h-screen
        bg-zinc-100
        dark:bg-zinc-950
        text-zinc-900
        dark:text-zinc-100
      "
    >

      <div
        className="
          max-w-3xl
          mx-auto
          px-6
          py-12
        "
      >

        {/* HEADER */}

        <div className="mb-10">

          <h1
            className="
              text-5xl
              font-black
            "
          >
            העלאת דוח שבועי
          </h1>

          <p
            className="
              mt-4
              text-zinc-600
              dark:text-zinc-400
              text-lg
            "
          >
            העלאת דוחות לצורך ניתוח AI תפעולי
          </p>

        </div>

        {/* CARD */}

        <div
          className="
            bg-white
            dark:bg-zinc-900
            border
            border-zinc-200
            dark:border-zinc-800
            rounded-3xl
            p-8
            shadow-sm
          "
        >

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

          <button
            onClick={uploadReport}

            disabled={
              uploading ||
              !selectedProject ||
              !selectedFile
            }

            className="
              w-full
              bg-zinc-900
              text-white
              dark:bg-white
              dark:text-black
              rounded-2xl
              py-4
              font-semibold
              text-lg
              disabled:opacity-50
              transition
            "
          >

            {uploading
              ? "מעלה דוח..."
              : "העלאת דוח ל-AI"}

          </button>

        </div>

      </div>

    </main>
  );
}