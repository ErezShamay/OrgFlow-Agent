"use client";

import { useEffect, useState } from "react";

type Review = {
  id: string;
  business_impact: string;
  tenant_risk: string;
  recommended_action: string;
  review_status: string;
};

export default function HomePage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/reviews/pending")
      .then((res) => res.json())
      .then((data) => {
        setReviews(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <main
      dir="rtl"
      className="
        min-h-screen
        bg-zinc-100
        dark:bg-zinc-950
        text-zinc-900
        dark:text-zinc-100
        transition-colors
      "
    >
      <div className="max-w-6xl mx-auto px-6 py-10">

        <div className="mb-10">
          <h1 className="text-5xl font-bold tracking-tight">
            OrgFlow
          </h1>

          <p className="text-zinc-600 dark:text-zinc-400 mt-3 text-lg">
            מרכז תפעול מבוסס AI
          </p>
        </div>

        {loading && (
          <div className="text-lg">
            טוען ביקורות...
          </div>
        )}

        {!loading && reviews.length === 0 && (
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
            אין ביקורות ממתינות
          </div>
        )}

        <div className="grid gap-6">

          {reviews.map((review) => (

            <div
              key={review.id}
              className="
                rounded-3xl
                border
                border-zinc-200
                dark:border-zinc-800
                bg-white
                dark:bg-zinc-900
                p-8
                shadow-sm
                hover:shadow-lg
                transition-all
              "
            >

              <div className="flex items-start justify-between mb-6">

                <div>

                  <h2 className="text-2xl font-semibold">
                    סקירת AI
                  </h2>

                  <p
                    className="
                      text-sm
                      text-zinc-500
                      dark:text-zinc-400
                      mt-1
                    "
                  >
                    {review.id}
                  </p>

                </div>

                <div
                  className="
                    px-4
                    py-2
                    rounded-full
                    text-sm
                    font-semibold
                    bg-yellow-100
                    text-yellow-800
                    dark:bg-yellow-900/40
                    dark:text-yellow-300
                  "
                >
                  {
                    review.review_status === "PENDING"
                      ? "ממתין לבדיקה"
                      : review.review_status === "APPROVED"
                      ? "אושר"
                      : review.review_status === "REJECTED"
                      ? "נדחה"
                      : review.review_status
                  }
                </div>

              </div>

              <div className="space-y-6">

                <div>

                  <h3 className="font-semibold text-lg mb-2">
                    השפעה עסקית
                  </h3>

                  <p
                    className="
                      text-zinc-700
                      dark:text-zinc-300
                      leading-relaxed
                    "
                  >
                    {review.business_impact}
                  </p>

                </div>

                <div>

                  <h3 className="font-semibold text-lg mb-2">
                    סיכון לדיירים
                  </h3>

                  <p
                    className="
                      text-zinc-700
                      dark:text-zinc-300
                      leading-relaxed
                    "
                  >
                    {review.tenant_risk}
                  </p>

                </div>

                <div>

                  <h3 className="font-semibold text-lg mb-2">
                    פעולה מומלצת
                  </h3>

                  <p
                    className="
                      text-zinc-700
                      dark:text-zinc-300
                      leading-relaxed
                    "
                  >
                    {review.recommended_action}
                  </p>

                </div>

              </div>

              <div className="flex gap-4 mt-8">

                <button
                  className="
                    bg-green-600
                    hover:bg-green-700
                    text-white
                    px-5
                    py-3
                    rounded-2xl
                    font-medium
                    transition-colors
                  "
                >
                  אישור
                </button>

                <button
                  className="
                    bg-red-600
                    hover:bg-red-700
                    text-white
                    px-5
                    py-3
                    rounded-2xl
                    font-medium
                    transition-colors
                  "
                >
                  דחייה
                </button>

              </div>

            </div>

          ))}

        </div>

      </div>
    </main>
  );
}