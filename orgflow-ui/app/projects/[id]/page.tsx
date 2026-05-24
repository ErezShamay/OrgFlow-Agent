"use client";

import { useEffect, useState } from "react";

import { useParams } from "next/navigation";

import ProjectTabs from "@/app/components/project-tabs";

type Project = {
  id: string;
  project_name: string;
  supervisor_name: string;
  supervisor_email: string;
  status: string;
  created_at: string;
};

type Review = {
  id: string;
  business_impact: string;
  tenant_risk: string;
  recommended_action: string;
  review_status: string;
};

type Summary = {
  reviews_count: number;
  actions_count: number;
  escalations_count: number;
  reports_count: number;
};

export default function ProjectDetailsPage() {

  const params = useParams();

  const projectId =
    params.id as string;

  const [project, setProject] =
    useState<Project | null>(null);

  const [reviews, setReviews] =
    useState<Review[]>([]);

  const [summary, setSummary] =
    useState<Summary>({
      reviews_count: 0,
      actions_count: 0,
      escalations_count: 0,
      reports_count: 0,
    });

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {

    if (!projectId) {
      return;
    }

    loadProject();

  }, [projectId]);

  async function loadProject() {

    try {

      // =========================
      // PROJECT
      // =========================

      const response = await fetch(
        `http://127.0.0.1:8000/projects/${projectId}`
      );

      const data =
        await response.json();

      setProject(data);

      // =========================
      // PROJECT REVIEWS
      // =========================

      const reviewsResponse =
        await fetch(
          `http://127.0.0.1:8000/projects/${projectId}/reviews`
        );

      const reviewsData =
        await reviewsResponse.json();

      setReviews(reviewsData);

      // =========================
      // PROJECT SUMMARY
      // =========================

      const summaryResponse =
        await fetch(
          `http://127.0.0.1:8000/projects/${projectId}/summary`
        );

      const summaryData =
        await summaryResponse.json();

      setSummary(summaryData);

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

      {/* PROJECT TABS */}

      <ProjectTabs
        projectId={projectId}
      />

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
            הסלמות
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
}