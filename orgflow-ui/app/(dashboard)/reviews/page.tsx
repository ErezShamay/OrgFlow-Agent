"use client";

import { useEffect, useState } from "react";

type Review = {
  id: string;
  business_impact: string;
  tenant_risk: string;
  recommended_action: string;
  review_status: string;
  created_at: string;
  model_name: string;
};

export default function ReviewsPage() {

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
        `${process.env.NEXT_PUBLIC_API_URL}/reviews/pending`
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

      {/* HEADER */}

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
          ביקורות הממתינות לאישור
          במערכת התפעול
        </p>

      </div>

      {/* KPI */}

      <div
        className="
          grid
          grid-cols-1
          md:grid-cols-3
          gap-6
          mb-10
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
            ביקורות ממתינות
          </p>

          <h2
            className="
              text-5xl
              font-black
            "
          >
            {reviews.length}
          </h2>

        </div>

        <div
          className="
            bg-white
            dark:bg-zinc-900
            border
            border-orange-200
            dark:border-orange-900
            rounded-3xl
            p-8
          "
        >

          <p
            className="
              text-orange-500
              mb-3
            "
          >
            דורש טיפול
          </p>

          <h2
            className="
              text-5xl
              font-black
            "
          >
            {reviews.length}
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
            מודל AI פעיל
          </p>

          <h2
            className="
              text-2xl
              font-bold
            "
          >
            Mistral AI
          </h2>

        </div>

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
            border
            border-zinc-200
            dark:border-zinc-800
            rounded-3xl
            p-10
          "
        >

          אין ביקורות ממתינות

        </div>

      )}

      {/* REVIEWS */}

      <div className="space-y-8">

        {reviews.map((review) => (

          <div
            key={review.id}
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

            {/* TOP */}

            <div
              className="
                flex
                justify-between
                items-start
                mb-8
              "
            >

              <div>

                <h2
                  className="
                    text-3xl
                    font-black
                  "
                >
                  ביקורת AI
                </h2>

                <p
                  className="
                    mt-2
                    text-zinc-500
                  "
                >
                  {new Date(
                    review.created_at
                  ).toLocaleString(
                    "he-IL"
                  )}
                </p>

              </div>

              <div
                className="
                  bg-orange-100
                  text-orange-700
                  dark:bg-orange-900/40
                  dark:text-orange-300
                  px-4
                  py-2
                  rounded-full
                  font-semibold
                "
              >
                ממתין לאישור
              </div>

            </div>

            {/* CONTENT */}

            <div className="space-y-8">

              <div>

                <h3
                  className="
                    text-lg
                    font-bold
                    mb-3
                  "
                >
                  השפעה עסקית
                </h3>

                <p
                  className="
                    leading-relaxed
                    text-lg
                  "
                >
                  {review.business_impact}
                </p>

              </div>

              <div>

                <h3
                  className="
                    text-lg
                    font-bold
                    mb-3
                  "
                >
                  סיכון לדיירים
                </h3>

                <p
                  className="
                    leading-relaxed
                    text-lg
                  "
                >
                  {review.tenant_risk}
                </p>

              </div>

              <div>

                <h3
                  className="
                    text-lg
                    font-bold
                    mb-3
                  "
                >
                  פעולה מומלצת
                </h3>

                <p
                  className="
                    leading-relaxed
                    text-lg
                  "
                >
                  {review.recommended_action}
                </p>

              </div>

            </div>

            {/* ACTIONS */}

            <div
              className="
                flex
                gap-4
                mt-10
              "
            >

              <button
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