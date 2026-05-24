"use client";

import Link from "next/link";

import { useEffect, useState } from "react";

type Project = {
  id: string;
  project_name: string;
  status: string;
};

type Organization = {
  id: string;
  organization_name: string;
  contact_email: string;
  projects: Project[];
};

export default function HomePage() {

  const [organizations, setOrganizations] =
    useState<Organization[]>([]);

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {
    loadOrganizations();
  }, []);

  async function loadOrganizations() {

    try {

      const response = await fetch(
        "http://127.0.0.1:8000/organizations"
      );

      const data =
        await response.json();

      setOrganizations(data);

    } catch (error) {

      console.error(error);

    } finally {

      setLoading(false);

    }
  }

  const totalProjects =
    organizations.reduce(
      (acc, org) =>
        acc + org.projects.length,
      0
    );

  const totalOrganizations =
    organizations.length;

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

      {/* HERO */}

      <section
        className="
          px-10
          pt-24
          pb-16
        "
      >

        <div className="max-w-7xl mx-auto">

          <div
            className="
              max-w-4xl
            "
          >

            <div
              className="
                inline-flex
                items-center
                gap-2
                bg-white
                dark:bg-zinc-900
                border
                border-zinc-200
                dark:border-zinc-800
                rounded-full
                px-4
                py-2
                mb-8
                text-sm
                font-medium
              "
            >
              מערכת תפעול הנדסי מבוססת AI
            </div>

            <h1
              className="
                text-6xl
                font-black
                leading-tight
                tracking-tight
              "
            >
              OrgFlow
            </h1>

            <p
              className="
                mt-8
                text-2xl
                leading-relaxed
                text-zinc-600
                dark:text-zinc-400
                max-w-3xl
              "
            >
              פלטפורמת AI לניהול תפעולי,
              פיקוח הנדסי, בקרת פרויקטים,
              ניתוח חריגות והסלמות
              בפרויקטי התחדשות עירונית ובנייה.
            </p>

          </div>

        </div>

      </section>

      {/* KPI SECTION */}

      <section className="px-10 pb-16">

        <div
          className="
            max-w-7xl
            mx-auto
            grid
            grid-cols-1
            md:grid-cols-2
            xl:grid-cols-4
            gap-6
          "
        >

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

            <p
              className="
                text-zinc-500
                mb-3
              "
            >
              חברות פעילות
            </p>

            <h2
              className="
                text-5xl
                font-black
              "
            >
              {totalOrganizations}
            </h2>

          </div>

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

            <p
              className="
                text-zinc-500
                mb-3
              "
            >
              פרויקטים פעילים
            </p>

            <h2
              className="
                text-5xl
                font-black
              "
            >
              {totalProjects}
            </h2>

          </div>

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

            <p
              className="
                text-zinc-500
                mb-3
              "
            >
              מנוע AI פעיל
            </p>

            <h2
              className="
                text-2xl
                font-bold
              "
            >
              Operational AI
            </h2>

          </div>

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

            <p
              className="
                text-zinc-500
                mb-3
              "
            >
              סטטוס מערכת
            </p>

            <h2
              className="
                text-2xl
                font-bold
              "
            >
              Online
            </h2>

          </div>

        </div>

      </section>

      {/* ORGANIZATIONS */}

      <section className="px-10 pb-24">

        <div className="max-w-7xl mx-auto">

          <div className="mb-10">

            <h2
              className="
                text-4xl
                font-black
              "
            >
              חברות ופרויקטים
            </h2>

            <p
              className="
                mt-3
                text-lg
                text-zinc-600
                dark:text-zinc-400
              "
            >
              גישה לפרויקטים הפעילים במערכת
            </p>

          </div>

          {loading && (
            <div>
              טוען נתונים...
            </div>
          )}

          <div className="space-y-10">

            {organizations.map((organization) => (

              <div
                key={organization.id}
                className="
                  bg-white
                  dark:bg-zinc-900
                  border
                  border-zinc-200
                  dark:border-zinc-800
                  rounded-[2rem]
                  p-10
                "
              >

                {/* ORGANIZATION HEADER */}

                <div className="mb-8">

                  <h3
                    className="
                      text-3xl
                      font-bold
                    "
                  >
                    {organization.organization_name}
                  </h3>

                  <p
                    className="
                      mt-2
                      text-zinc-500
                    "
                  >
                    {organization.contact_email}
                  </p>

                </div>

                {/* PROJECTS */}

                <div
                  className="
                    grid
                    grid-cols-1
                    lg:grid-cols-2
                    xl:grid-cols-3
                    gap-6
                  "
                >

                  {organization.projects.map(
                    (project) => (

                    <Link
                      key={project.id}
                      href={`/projects/${project.id}`}
                      className="
                        bg-zinc-50
                        dark:bg-zinc-800/50
                        rounded-3xl
                        p-8
                        border
                        border-zinc-200
                        dark:border-zinc-800
                        hover:shadow-lg
                        transition-all
                        hover:-translate-y-1
                      "
                    >

                      <div
                        className="
                          flex
                          justify-between
                          items-start
                          mb-5
                        "
                      >

                        <h4
                          className="
                            text-2xl
                            font-bold
                          "
                        >
                          {project.project_name}
                        </h4>

                        <div
                          className="
                            bg-green-100
                            text-green-700
                            dark:bg-green-900/40
                            dark:text-green-300
                            px-3
                            py-1
                            rounded-full
                            text-sm
                            font-semibold
                          "
                        >
                          פעיל
                        </div>

                      </div>

                      <p
                        className="
                          text-zinc-500
                        "
                      >
                        כניסה לסביבת העבודה
                        התפעולית של הפרויקט
                      </p>

                    </Link>

                  ))}

                </div>

              </div>

            ))}

          </div>

        </div>

      </section>

    </main>
  );
}