"use client";

import { useParams } from "next/navigation";

import { useProjectWorkspace } from "@/hooks/useProjectWorkspace";

import ProjectActivityTimeline from "@/components/projects/ProjectActivityTimeline";

import ProjectInsightsPanel from "@/components/projects/ProjectInsightsPanel";

export default function ProjectDetailsPage() {

  const params = useParams();

  const projectId =
    params.id as string;

  const {
    project,
    reviews,
    activities,
    insights,
    summary,
    loading,
  } = useProjectWorkspace(
    projectId
  );

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

  if (loading) {

    return (
      <main
        className="
          p-10
          text-zinc-900
          dark:text-zinc-100
        "
      >
        טוען פרויקט...
      </main>
    );
  }

  if (!project) {

    return (
      <main
        className="
          p-10
          text-zinc-900
          dark:text-zinc-100
        "
      >
        פרויקט לא נמצא
      </main>
    );
  }

  return (

    <main
      className="
        p-10
        text-zinc-900
        dark:text-zinc-100
      "
    >

      {/* PROJECT HEADER */}

      <div
        className="
          bg-white
          dark:bg-zinc-900
          border
          border-zinc-200
          dark:border-zinc-800
          rounded-3xl
          p-10
          shadow-sm
        "
      >

        <div
          className="
            flex
            justify-between
            items-start
            mb-8
          "
        >

          <div>

            <h1
              className="
                text-5xl
                font-bold
              "
            >
              {project.project_name}
            </h1>

            <p
              className="
                mt-4
                text-zinc-600
                dark:text-zinc-400
                text-lg
              "
            >
              סביבת עבודה תפעולית לפרויקט
            </p>

          </div>

          <div
            className="
              bg-green-100
              text-green-700
              dark:bg-green-900/40
              dark:text-green-300
              px-5
              py-3
              rounded-full
              font-semibold
            "
          >
            {getStatusLabel(
              project.status
            )}
          </div>

        </div>

        <div
          className="
            grid
            grid-cols-1
            md:grid-cols-3
            gap-6
          "
        >

          <div
            className="
              bg-zinc-50
              dark:bg-zinc-800/50
              rounded-2xl
              p-6
            "
          >

            <h3
              className="
                font-semibold
                mb-3
              "
            >
              מפקח אחראי
            </h3>

            <p>
              {project.supervisor_name}
            </p>

          </div>

          <div
            className="
              bg-zinc-50
              dark:bg-zinc-800/50
              rounded-2xl
              p-6
            "
          >

            <h3
              className="
                font-semibold
                mb-3
              "
            >
              אימייל מפקח
            </h3>

            <p>
              {project.supervisor_email}
            </p>

          </div>

          <div
            className="
              bg-zinc-50
              dark:bg-zinc-800/50
              rounded-2xl
              p-6
            "
          >

            <h3
              className="
                font-semibold
                mb-3
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

      {/* KPI CARDS */}

      <div
        className="
          grid
          grid-cols-1
          md:grid-cols-2
          xl:grid-cols-4
          gap-6
          mt-10
        "
      >

        <KpiCard
          title="ביקורות AI"
          value={summary.reviews_count}
        />

        <KpiCard
          title="פעולות פתוחות"
          value={summary.actions_count}
        />

        <KpiCard
          title="נקודות סיכון"
          value={summary.escalations_count}
          danger
        />

        <KpiCard
          title="דוחות שהתקבלו"
          value={summary.reports_count}
        />

      </div>

      {/* HEALTH */}

      <div
        className="
          mt-10
          bg-white
          dark:bg-zinc-900
          border
          border-zinc-200
          dark:border-zinc-800
          rounded-3xl
          p-10
        "
      >

        <p
          className="
            text-zinc-500
            mb-3
          "
        >
          מצב הפרויקט
        </p>

        <h2
          className="
            text-4xl
            font-black
          "
        >
          {summary.escalations_count > 3
            ? "קריטי"

            : summary.escalations_count > 0
            ? "דורש טיפול"

            : "יציב"}
        </h2>

      </div>

      {/* INSIGHTS */}

      <div className="mt-10">

        <ProjectInsightsPanel
          insights={insights}
        />

      </div>

      {/* TIMELINE */}

      <div className="mt-10">

        <ProjectActivityTimeline
          activities={activities}
        />

      </div>

      {/* REVIEWS */}

      <div className="mt-10">

        <h2
          className="
            text-3xl
            font-bold
            mb-6
          "
        >
          ביקורות AI בפרויקט
        </h2>

        {reviews.length === 0 && (

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
            אין ביקורות בפרויקט
          </div>

        )}

        <div className="grid gap-6">

          {reviews.map((review) => (

            <div
              key={review.id}
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

              <div className="space-y-5">

                <div>

                  <h3
                    className="
                      font-semibold
                      mb-2
                    "
                  >
                    השפעה עסקית
                  </h3>

                  <p>
                    {review.business_impact}
                  </p>

                </div>

                <div>

                  <h3
                    className="
                      font-semibold
                      mb-2
                    "
                  >
                    סיכון לדיירים
                  </h3>

                  <p>
                    {review.tenant_risk}
                  </p>

                </div>

                <div>

                  <h3
                    className="
                      font-semibold
                      mb-2
                    "
                  >
                    פעולה מומלצת
                  </h3>

                  <p>
                    {review.recommended_action}
                  </p>

                </div>

              </div>

            </div>

          ))}

        </div>

      </div>

    </main>
  );
}

type KpiCardProps = {
  title: string;
  value: number;
  danger?: boolean;
};

function KpiCard({
  title,
  value,
  danger,
}: KpiCardProps) {

  return (

    <div
      className={`
        bg-white
        dark:bg-zinc-900
        border
        rounded-3xl
        p-8

        ${
          danger
            ? `
              border-red-200
              dark:border-red-900
            `
            : `
              border-zinc-200
              dark:border-zinc-800
            `
        }
      `}
    >

      <p
        className={`
          mb-3

          ${
            danger
              ? "text-red-500"
              : "text-zinc-500"
          }
        `}
      >
        {title}
      </p>

      <h2
        className={`
          text-5xl
          font-black

          ${
            danger
              ? "text-red-600"
              : ""
          }
        `}
      >
        {value}
      </h2>

    </div>

  );
}