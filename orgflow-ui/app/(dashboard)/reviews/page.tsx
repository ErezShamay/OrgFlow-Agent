"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/contexts/AuthContext";
import { apiFetch } from "@/lib/api/client";
import { showToast } from "@/lib/ui/toast";

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
  const { profile } = useAuth();

  const [reviews, setReviews] =
    useState<Review[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [processingId, setProcessingId] =
    useState<string | null>(null);

  useEffect(() => {
    void loadReviews();
  }, []);

  async function loadReviews() {
    try {
      const response = await apiFetch("/reviews/pending");

      const data =
        await response.json();

      setReviews(data);

    } catch (error) {

      console.error(error);

    } finally {

      setLoading(false);

    }
  }

  async function approveReview(reviewId: string) {
    setProcessingId(reviewId);

    try {
      const response = await apiFetch(
        `/reviews/${reviewId}/approve`,
        {
          method: "POST",
          body: JSON.stringify({
            reviewed_by:
              profile?.full_name ||
              profile?.email ||
              profile?.id ||
              "reviewer",
            review_notes: "Approved from reviews dashboard",
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Approve failed");
      }

      setReviews((current) =>
        current.filter((review) => review.id !== reviewId)
      );
      showToast("הביקורת אושרה בהצלחה", "success");
    } catch (error) {
      console.error(error);
      showToast("שגיאה באישור הביקורת", "error");
    } finally {
      setProcessingId(null);
    }
  }

  async function rejectReview(reviewId: string) {
    setProcessingId(reviewId);

    try {
      const response = await apiFetch(
        `/reviews/${reviewId}/reject`,
        {
          method: "POST",
          body: JSON.stringify({
            reviewed_by:
              profile?.full_name ||
              profile?.email ||
              profile?.id ||
              "reviewer",
            review_notes: "Rejected from reviews dashboard",
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Reject failed");
      }

      setReviews((current) =>
        current.filter((review) => review.id !== reviewId)
      );
      showToast("הביקורת נדחתה", "success");
    } catch (error) {
      console.error(error);
      showToast("שגיאה בדחיית הביקורת", "error");
    } finally {
      setProcessingId(null);
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
                disabled={processingId === review.id}
                onClick={() => approveReview(review.id)}
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
                  disabled:opacity-50
                "
              >
                אישור ביקורת
              </button>

              <button
                disabled={processingId === review.id}
                onClick={() => rejectReview(review.id)}
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
                  disabled:opacity-50
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