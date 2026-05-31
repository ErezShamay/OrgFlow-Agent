"use client";

import { use } from "react";
import Button from "@/components/ui/Button";
import { useProjectWorkspace } from "@/hooks/useProjectWorkspace";

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

  const {
    reviews,
    loading,
    approveReview,
  } = useProjectWorkspace(
    projectId
  );

  return (
    <main className="of-dashboard-page">

      <div className="mb-10">

        <h1 className="of-page-title">
          ביקורות AI
        </h1>

        <p className="of-page-desc mt-4">
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

        <div className="of-card of-card-p8">
          אין ביקורות AI פתוחות
        </div>

      )}

      {/* REVIEWS */}

      <div className="grid gap-6">

        {reviews.map((review) => (

          <div
            key={review.id}
            className="of-card of-card-p8"
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

              <Button
                variant="primary"
                size="lg"
                onClick={() =>
                  approveReview(
                    review.id
                  )
                }
              >
                אישור ביקורת
              </Button>

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
