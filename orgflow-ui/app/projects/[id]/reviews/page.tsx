"use client";

import { useEffect, useState } from "react";

import ProjectTabs from "@/app/components/project-tabs";

type Review = {
  id: string;
  business_impact: string;
  tenant_risk: string;
  recommended_action: string;
};

export default function ReviewsPage({
  params,
}: {
  params: {
    id: string;
  };
}) {

  const [reviews, setReviews] =
    useState<Review[]>([]);

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {
    loadReviews();
  }, []);

  async function loadReviews() {

    try {

      const response = await fetch(
        `http://127.0.0.1:8000/projects/${params.id}/reviews`
      );

      const data =
        await response.json();

      setReviews(data);

    } catch (error) {

      console.error(error);

    } finally {

      setLoading(false);

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

      <ProjectTabs
        projectId={params.id}
      />

      <div className="mb-10">

        <h1
          className="
            text-5xl
            font-black
          "
        >
          ביקורות AI
        </h1>

        <p
          className="
            mt-4
            text-zinc-500
            text-lg
          "
        >
          ביקורות והמלצות שנוצרו על ידי מנוע ה-AI
        </p>

      </div>

      {loading && (
        <div>
          טוען ביקורות...
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

    </main>
  );
}