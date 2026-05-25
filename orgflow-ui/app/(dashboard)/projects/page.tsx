"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type Project = {
  id: string;
  project_name: string;
  supervisor_name: string;
  supervisor_email: string;
  status: string;
  created_at: string;
};

export default function ProjectsPage() {
  const [projects, setProjects] =
    useState<Project[]>([]);

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/projects`
      );

      const data = await response.json();

      setProjects(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  function getStatusLabel(
    status: string
  ) {
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
    <main
      className="
        p-10
        text-zinc-900
        dark:text-zinc-100
      "
    >
      <div className="mb-10">

        <h1 className="text-5xl font-bold">
          פרויקטים
        </h1>

        <p
          className="
            mt-3
            text-lg
            text-zinc-600
            dark:text-zinc-400
          "
        >
          ניהול פרויקטים הנדסיים במערכת
        </p>

      </div>

      {loading && (
        <div>
          טוען פרויקטים...
        </div>
      )}

      {!loading &&
        projects.length === 0 && (
          <div
            className="
              bg-white
              dark:bg-zinc-900
              border
              border-zinc-200
              dark:border-zinc-800
              rounded-3xl
              p-8
            "
          >
            אין פרויקטים
          </div>
        )}

      <div className="grid gap-6">

        {projects.map((project) => (

          <div
            key={project.id}
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

            <div
              className="
                flex
                justify-between
                items-start
                mb-6
              "
            >

              <div>

                <h2
                  className="
                    text-2xl
                    font-semibold
                  "
                >
                  {project.project_name}
                </h2>

                <p
                  className="
                    text-zinc-500
                    mt-2
                  "
                >
                  {project.supervisor_name}
                </p>

              </div>

              <div
                className="
                  bg-green-100
                  text-green-700
                  dark:bg-green-900/40
                  dark:text-green-300
                  px-4
                  py-2
                  rounded-full
                  text-sm
                  font-semibold
                "
              >
                {getStatusLabel(
                  project.status
                )}
              </div>

            </div>

            <div className="space-y-4">

              <div>

                <h3
                  className="
                    font-semibold
                    mb-2
                  "
                >
                  אימייל מפקח
                </h3>

                <p>
                  {project.supervisor_email}
                </p>

              </div>

              <div>

                <h3
                  className="
                    font-semibold
                    mb-2
                  "
                >
                  תאריך יצירה
                </h3>

                <p>
                  {new Date(
                    project.created_at
                  ).toLocaleDateString(
                    "he-IL"
                  )}
                </p>

              </div>

            </div>

          </div>

        ))}

      </div>

    </main>
  );
} 