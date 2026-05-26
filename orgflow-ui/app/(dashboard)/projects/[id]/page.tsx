"use client";

import { useParams } from "next/navigation";

import { useProjectWorkspace } from "@/hooks/useProjectWorkspace";

import ProjectActivityTimeline from "@/components/projects/ProjectActivityTimeline";

export default function ProjectDetailsPage() {

  const params = useParams();

  const projectId =
    params.id as string;

  const {
  project,
  reviews,
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

      {/* PROJECT DETAILS */}

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
            ביקורות AI
          </p>

          <h2
            className="
              text-5xl
              font-black
            "
          >
            {summary.reviews_count}
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
            פעולות פתוחות
          </p>

          <h2
            className="
              text-5xl
              font-black
            "
          >
            {summary.actions_count}
          </h2>

        </div>

        <div
          className="
            bg-white
            dark:bg-zinc-900
            border
            border-red-200
            dark:border-red-900
            rounded-3xl
            p-8
          "
        >

          <p
            className="
              text-red-500
              mb-3
            "
          >
            נקודות סיכון
          </p>

          <h2
            className="
              text-5xl
              font-black
              text-red-600
            "
          >
            {summary.escalations_count}
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
            דוחות שהתקבלו
          </p>

          <h2
            className="
              text-5xl
              font-black
            "
          >
            {summary.reports_count}
          </h2>

        </div>

      </div>

      {/* PROJECT HEALTH */}

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

        <div
          className="
            flex
            justify-between
            items-center
          "
        >

          <div>

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

          <div
            className={`
              w-5
              h-5
              rounded-full

              ${
                summary.escalations_count > 3
                  ? "bg-red-500"

                  : summary.escalations_count > 0
                  ? "bg-yellow-500"

                  : "bg-green-500"
              }
            `}
          />

        </div>

        <p
          className="
            mt-6
            text-zinc-600
            dark:text-zinc-400
            leading-relaxed
          "
        >

          {summary.escalations_count > 3
            ? "המערכת זיהתה מספר חריגות משמעותיות הדורשות טיפול מיידי."

            : summary.escalations_count > 0
            ? "קיימות נקודות סיכון/חריגות פתוחות בפרויקט."

            : "לא זוהו חריגות משמעותיות בפרויקט."}

        </p>

      </div>

      {/* PROJECT REVIEWS */}

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

  {/* QUICK ACTIONS */}

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

  <div className="mb-8">

    <h2
      className="
        text-3xl
        font-bold
      "
    >
      פעולות מהירות
    </h2>

    <p
      className="
        mt-3
        text-zinc-500
      "
    >
      גישה מהירה לפעולות מרכזיות בפרויקט
    </p>

  </div>

  <div
    className="
      grid
      grid-cols-1
      md:grid-cols-2
      gap-5
    "
  >

    <a
      href={`/projects/${projectId}/reviews`}
      className="
        bg-zinc-50
        dark:bg-zinc-800/50
        border
        border-zinc-200
        dark:border-zinc-700
        rounded-2xl
        p-6
        hover:bg-zinc-100
        dark:hover:bg-zinc-800
        transition
      "
    >

      <h3
        className="
          text-xl
          font-semibold
          mb-2
        "
      >
        ביקורות AI
      </h3>

      <p
        className="
          text-zinc-500
        "
      >
        צפייה ואישור ביקורות AI
      </p>

    </a>

    <a
      href={`/projects/${projectId}/actions`}
      className="
        bg-zinc-50
        dark:bg-zinc-800/50
        border
        border-zinc-200
        dark:border-zinc-700
        rounded-2xl
        p-6
        hover:bg-zinc-100
        dark:hover:bg-zinc-800
        transition
      "
    >

      <h3
        className="
          text-xl
          font-semibold
          mb-2
        "
      >
        פעולות תפעוליות
      </h3>

      <p
        className="
          text-zinc-500
        "
      >
        צפייה בפעולות פתוחות
      </p>

    </a>

    <a
      href={`/projects/${projectId}/exceptions`}
      className="
        bg-zinc-50
        dark:bg-zinc-800/50
        border
        border-zinc-200
        dark:border-zinc-700
        rounded-2xl
        p-6
        hover:bg-zinc-100
        dark:hover:bg-zinc-800
        transition
      "
    >

      <h3
        className="
          text-xl
          font-semibold
          mb-2
        "
      >
        חריגות
      </h3>

      <p
        className="
          text-zinc-500
        "
      >
        צפייה בנקודות סיכון בפרויקט
      </p>

    </a>

    <div
      className="
        bg-zinc-50
        dark:bg-zinc-800/50
        border
        border-dashed
        border-zinc-300
        dark:border-zinc-700
        rounded-2xl
        p-6
      "
    >

      <h3
        className="
          text-xl
          font-semibold
          mb-2
        "
      >
        העלאת דוח
      </h3>

      <p
        className="
          text-zinc-500
        "
      >
        בקרוב תהיה אפשרות להעלות דוחות ידנית
      </p>

    </div>

  </div>

</div>

  {/* RECENT ACTIVITY */}

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

  <div className="mb-8">

    <h2
      className="
        text-3xl
        font-bold
      "
    >
      פעילות אחרונה
    </h2>

    <p
      className="
        mt-3
        text-zinc-500
      "
    >
      אירועים אחרונים בפרויקט
    </p>

  </div>

  <div className="space-y-5">

    {summary.reviews_count > 0 && (

      <div
        className="
          flex
          items-center
          gap-4
          p-5
          rounded-2xl
          bg-zinc-50
          dark:bg-zinc-800/50
        "
      >

        <div
          className="
            w-3
            h-3
            rounded-full
            bg-blue-500
          "
        />

        <p>
          התקבלו
          {" "}
          {summary.reviews_count}
          {" "}
          ביקורות AI בפרויקט
        </p>

      </div>

    )}

    {summary.actions_count > 0 && (

      <div
        className="
          flex
          items-center
          gap-4
          p-5
          rounded-2xl
          bg-zinc-50
          dark:bg-zinc-800/50
        "
      >

        <div
          className="
            w-3
            h-3
            rounded-full
            bg-yellow-500
          "
        />

        <p>
          קיימות
          {" "}
          {summary.actions_count}
          {" "}
          פעולות פתוחות לטיפול
        </p>

      </div>

    )}

    {summary.escalations_count > 0 && (

      <div
        className="
          flex
          items-center
          gap-4
          p-5
          rounded-2xl
          bg-red-50
          dark:bg-red-900/20
        "
      >

        <div
          className="
            w-3
            h-3
            rounded-full
            bg-red-500
          "
        />

        <p>
          זוהו
          {" "}
          {summary.escalations_count}
          {" "}
          נקודות סיכון בפרויקט
        </p>

      </div>

    )}

    {summary.reports_count > 0 && (

      <div
        className="
          flex
          items-center
          gap-4
          p-5
          rounded-2xl
          bg-zinc-50
          dark:bg-zinc-800/50
        "
      >

        <div
          className="
            w-3
            h-3
            rounded-full
            bg-green-500
          "
        />

        <p>
          התקבלו
          {" "}
          {summary.reports_count}
          {" "}
          דוחות בפרויקט
        </p>

      </div>

    )}

  </div>

</div>
}