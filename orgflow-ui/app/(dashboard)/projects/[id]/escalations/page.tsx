"use client";

import { use } from "react";

import { useProjectWorkspace } from "@/hooks/useProjectWorkspace";

type Props = {
  params: Promise<{
    id: string;
  }>;
};

export default function ProjectEscalationsPage({
  params,
}: Props) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;

  const {
    exceptions,
    loading,
    escalateAction,
  } = useProjectWorkspace(projectId);

  return (
    <main
      className="
        p-10
        text-zinc-900
        dark:text-zinc-100
      "
    >
      <div className="mb-10">
        <h1 className="text-5xl font-black">
          נקודות סיכון
        </h1>

        <p
          className="
            mt-4
            text-lg
            text-zinc-500
          "
        >
          אירועים הדורשים טיפול מיידי בפרויקט
        </p>
      </div>

      {loading ? (
        <div>טוען נקודות סיכון...</div>
      ) : null}

      {!loading && exceptions.length === 0 ? (
        <div
          className="
            rounded-3xl
            border
            border-zinc-200
            bg-white
            p-10
            dark:border-zinc-800
            dark:bg-zinc-900
          "
        >
          אין נקודות סיכון פתוחות
        </div>
      ) : null}

      <div className="grid gap-6">
        {exceptions.map((action) => (
          <div
            key={action.id}
            className="
              rounded-3xl
              border
              border-orange-200
              bg-white
              p-8
              dark:border-orange-900
              dark:bg-zinc-900
            "
          >
            <h2 className="text-2xl font-bold">
              {action.title}
            </h2>

            <p className="mt-4 leading-relaxed">
              {action.description}
            </p>

            <div className="mt-6 flex gap-3">
              <button
                onClick={() => escalateAction(action.id)}
                className="
                  rounded-2xl
                  bg-orange-600
                  px-5
                  py-3
                  font-semibold
                  text-white
                "
              >
                הסלמה
              </button>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
