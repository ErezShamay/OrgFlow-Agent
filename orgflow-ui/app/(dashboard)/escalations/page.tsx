"use client";

import { useEffect, useState } from "react";

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

  useEffect(() => {
    loadEscalations();
  }, []);

  async function loadEscalations() {
    try {
      const response = await apiFetch("/actions/escalations");

      const data = await response.json();

      setEscalations(data);
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
      <div className="mb-10">

        <h1 className="text-5xl font-bold">
          נקודות סיכון
        </h1>

        <p
          className="
            mt-3
            text-lg
            text-zinc-600
            dark:text-zinc-400
          "
        >
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
            אין נקודות סיכון פתוחות
          </div>
        )}

      <div className="grid gap-6">

        {escalations.map(
          (escalation) => (

            <div
              key={escalation.id}
              className="
                bg-white
                dark:bg-zinc-900
                border
                border-red-200
                dark:border-red-900
                rounded-3xl
                p-8
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

                <div
                  className="
                    bg-red-100
                    text-red-700
                    dark:bg-red-900/40
                    dark:text-red-300
                    px-4
                    py-2
                    rounded-full
                    text-sm
                    font-semibold
                  "
                >
                  דחוף
                </div>

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