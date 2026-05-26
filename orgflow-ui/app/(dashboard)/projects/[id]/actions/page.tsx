"use client";

import { use } from "react";

import { useProjectWorkspace } from "@/hooks/useProjectWorkspace";

type Props = {
  params: Promise<{
    id: string;
  }>;
};

export default function ProjectActionsPage({
  params,
}: Props) {

  const resolvedParams =
    use(params);

  const projectId =
    resolvedParams.id;

  const {
    actions,
    loading,
    closeAction,
    reloadWorkspace,
  } = useProjectWorkspace(
    projectId
  );

  // =========================
  // LABELS
  // =========================

  function getActionTypeLabel(
    type: string
  ) {

    switch (type) {

      case "ESCALATION":
        return "נקודת סיכון";

      default:
        return type;
    }
  }

  function getStatusLabel(
    status: string
  ) {

    switch (status) {

      case "OPEN":
        return "פתוח";

      case "CLOSED":
        return "סגור";

      default:
        return status;
    }
  }

  // =========================
  // ASSIGN ACTION
  // =========================

  async function assignAction(
    actionId: string,
    assignedTo: string
  ) {

    try {

      const response =
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/actions/${actionId}/assign`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              assigned_to:
                assignedTo,
            }),
          }
        );

      if (!response.ok) {

        throw new Error(
          "Failed assigning action"
        );
      }

      await reloadWorkspace();

    } catch (error) {

      console.error(error);
    }
  }

  return (

    <main
      className="
        bg-zinc-100
        dark:bg-zinc-950
        text-zinc-900
        dark:text-zinc-100
        min-h-screen
      "
    >

      <div
        className="
          max-w-6xl
          mx-auto
          px-6
          py-10
        "
      >

        {/* HEADER */}

        <div className="mb-10">

          <h1
            className="
              text-5xl
              font-bold
            "
          >
            פעולות תפעוליות
          </h1>

          <p
            className="
              text-zinc-600
              dark:text-zinc-400
              mt-3
              text-lg
            "
          >
            ניהול משימות ופעולות בפרויקט
          </p>

        </div>

        {/* LOADING */}

        {loading && (

          <div>
            טוען פעולות...
          </div>

        )}

        {/* EMPTY */}

        {!loading &&
          actions.length === 0 && (

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
            אין פעולות פתוחות
          </div>

        )}

        {/* ACTIONS */}

        <div className="grid gap-6">

          {actions.map((action) => (

            <div
              key={action.id}
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

              {/* HEADER */}

              <div
                className="
                  flex
                  justify-between
                  items-start
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
                    {action.title}
                  </h2>

                  <p
                    className="
                      text-sm
                      text-zinc-500
                      mt-2
                      break-all
                    "
                  >
                    {action.id}
                  </p>

                </div>

                <div
                  className="
                    bg-blue-100
                    text-blue-800
                    dark:bg-blue-900/40
                    dark:text-blue-300
                    px-4
                    py-2
                    rounded-full
                    text-sm
                    font-semibold
                  "
                >
                  {getStatusLabel(
                    action.status
                  )}
                </div>

              </div>

              {/* CONTENT */}

              <div className="space-y-6">

                <div>

                  <h3
                    className="
                      font-semibold
                      mb-2
                    "
                  >
                    סוג פעולה
                  </h3>

                  <p>
                    {getActionTypeLabel(
                      action.action_type
                    )}
                  </p>

                </div>

                <div>

                  <h3
                    className="
                      font-semibold
                      mb-2
                    "
                  >
                    תיאור
                  </h3>

                  <p
                    className="
                      text-zinc-700
                      dark:text-zinc-300
                      leading-relaxed
                    "
                  >
                    {action.description}
                  </p>

                </div>

                {/* ASSIGNEE */}

                <div>

                  <h3
                    className="
                      font-semibold
                      mb-2
                    "
                  >
                    אחראי
                  </h3>

                  <p
                    className="
                      mb-4
                      text-zinc-600
                      dark:text-zinc-400
                    "
                  >
                    {action.assigned_to
                      || "לא הוגדר"}
                  </p>

                  <select
                    defaultValue={
                      action.assigned_to || ""
                    }

                    onChange={(event) =>
                      assignAction(
                        action.id,
                        event.target.value
                      )
                    }

                    className="
                      w-full
                      rounded-2xl
                      border
                      border-zinc-300
                      dark:border-zinc-700
                      bg-white
                      dark:bg-zinc-900
                      px-4
                      py-3
                    "
                  >

                    <option value="">
                      ללא שיוך
                    </option>

                    <option value="ארז שמאי">
                      ארז שמאי
                    </option>

                    <option value="מנהל אזור">
                      מנהל אזור
                    </option>

                    <option value="מפקח שטח">
                      מפקח שטח
                    </option>

                  </select>

                </div>

              </div>

              {/* ACTION BUTTONS */}

              <div className="mt-8">

                <button
                  onClick={() =>
                    closeAction(
                      action.id
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
                  סגירת פעולה
                </button>

              </div>

            </div>

          ))}

        </div>

      </div>

    </main>
  );
}