"use client";

import {
  use,
  useEffect,
  useState,
} from "react";

type Review = {
  id: string;
  business_impact: string;
  tenant_risk: string;
  recommended_action: string;
  review_status: string;
};

type Props = {
  params: Promise<{
    id: string;
  }>;
};

export default function ReviewsPage({
  params,
}: Props) {

  const resolvedParams =
    use(params);

  const projectId =
    resolvedParams.id;

  const [reviews, setReviews] =
    useState<Review[]>([]);

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {
    loadReviews();
  }, []);

  async function loadReviews() {

    try {

      const response =
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}/reviews`
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

  async function approveReview(
    reviewId: string
  ) {

    try {

      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/reviews/${reviewId}/approve`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            reviewed_by:
              "ארז שמאי",

            review_notes:
              "אושר דרך מערכת התפעול",
          }),
        }
      );

      setReviews(
        current =>
          current.filter(
            review =>
              review.id !== reviewId
          )
      );

    } catch (error) {

      console.error(error);

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
          "
        >
          סקירת הביקורות בפרויקט
        </p>

      </div>

      {/* LOADING */}

      {loading && (

        <div>
          טוען ביקורות...
        </div>

      )}

      {/* EMPTY */}

      {!loading &&
        reviews.length === 0 && (

        <div
          className="
            bg-white
            dark:bg-zinc-900
            rounded-3xl
            p-8
            border
            border-zinc-200
            dark:border-zinc-800
          "
        >
          אין ביקורות AI פתוחות
        </div>

      )}

      {/* REVIEWS */}

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

            {/* ACTIONS */}

            <div
              className="
                flex
                gap-4
                mt-8
              "
            >

              <button
                onClick={() =>
                  approveReview(
                    review.id
                  )
                }
                className="
                  bg-zinc-900
                  text-white
                  dark:bg-white
                  dark:text-black
                  px-6
                  py-3
                  rounded-2xl
                  font-semibold
                  hover:opacity-90
                  transition
                "
              >
                אישור ביקורת
              </button>

              <button
                className="
                  border
                  border-zinc-300
                  dark:border-zinc-700
                  px-6
                  py-3
                  rounded-2xl
                  font-semibold
                  hover:bg-zinc-100
                  dark:hover:bg-zinc-800
                  transition
                "
              >
                דחייה
              </button>

            </div>

          </div>

        ))}

      </div>

    </main>
  );
}