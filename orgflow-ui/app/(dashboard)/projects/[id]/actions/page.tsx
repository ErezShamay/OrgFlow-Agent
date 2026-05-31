"use client";

import { use } from "react";

import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { useProjectWorkspace } from "@/hooks/useProjectWorkspace";
import { apiFetch } from "@/lib/api/client";

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
        await apiFetch(
          `/actions/${actionId}/assign`,
          {
            method: "POST",
            body: JSON.stringify({
              assigned_to: assignedTo,
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

    <main className="of-dashboard-page">

      <div className="mx-auto max-w-6xl">

        {/* HEADER */}

        <div className="mb-10">

          <h1 className="of-page-title">
            פעולות תפעוליות
          </h1>

          <p className="of-page-desc mt-3">
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

          <div className="of-card of-card-p8">
            אין פעולות פתוחות
          </div>

        )}

        {/* ACTIONS */}

        <div className="grid gap-6">

          {actions.map((action) => (

            <div
              key={action.id}
              className="of-card of-card-p8 shadow-sm"
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

                <Badge variant="info">
                  {getStatusLabel(
                    action.status
                  )}
                </Badge>

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

                <Button
                  variant="primary"
                  size="lg"
                  onClick={() =>
                    closeAction(
                      action.id
                    )
                  }
                >
                  סגירת פעולה
                </Button>

              </div>

            </div>

          ))}

        </div>

      </div>

    </main>
  );
}