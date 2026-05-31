"use client";

import { useCallback, useEffect, useState, startTransition } from "react";

import Badge from "@/components/ui/Badge";
import { apiFetch } from "@/lib/api/client";

type Escalation = {
  id: string;
  title: string;
  description: string;
  status: string;
  created_at: string;
};

export default function EscalationsPage() {
  const [escalations, setEscalations] =
    useState<Escalation[]>([]);

  const [loading, setLoading] =
    useState(true);

  const loadEscalations = useCallback(async () => {
    try {
      const response = await apiFetch("/actions/escalations");

      const data = await response.json();

      setEscalations(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    startTransition(() => {
      void loadEscalations();
    });
  }, [loadEscalations]);

  return (
    <main className="of-dashboard-page">
      <div className="mb-10">

        <h1 className="of-page-title">
          נקודות סיכון
        </h1>

        <p className="of-page-desc mt-3">
          אירועים הדורשים טיפול מיידי
        </p>

      </div>

      {loading && (
        <div>
          טוען נקודות סיכון...
        </div>
      )}

      {!loading &&
        escalations.length === 0 && (
          <div className="of-card of-card-p8">
            אין נקודות סיכון פתוחות
          </div>
        )}

      <div className="grid gap-6">

        {escalations.map(
          (escalation) => (

            <div
              key={escalation.id}
              className="
                of-card
                of-card-p8
                border-red-200
                dark:border-red-900
                shadow-sm
              "
            >

              <div
                className="
                  flex
                  items-start
                  justify-between
                  mb-6
                "
              >

                <div>

                  <h2
                    className="
                      text-2xl
                      font-semibold
                    "
                  >
                    {escalation.title}
                  </h2>

                  <p
                    className="
                      text-sm
                      text-zinc-500
                      mt-2
                    "
                  >
                    {new Date(
                      escalation.created_at
                    ).toLocaleString(
                      "he-IL"
                    )}
                  </p>

                </div>

                <Badge variant="danger">
                  דחוף
                </Badge>

              </div>

              <div>

                <h3
                  className="
                    font-semibold
                    mb-3
                  "
                >
                  תיאור האירוע
                </h3>

                <p
                  className="
                    text-zinc-700
                    dark:text-zinc-300
                    leading-relaxed
                  "
                >
                  {escalation.description}
                </p>

              </div>

            </div>

          )
        )}

      </div>

    </main>
  );
}
