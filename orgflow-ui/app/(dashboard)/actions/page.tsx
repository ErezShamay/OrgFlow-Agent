"use client";

import Link from "next/link";

import {
  useEffect,
  useState,
} from "react";

import Badge from "@/components/ui/Badge";

import {
  useAuth,
} from "@/contexts/AuthContext";

import { apiFetch } from "@/lib/api/client";
import {
  canEscalateActions,
  canManageActions,
} from "@/lib/auth/permissions";

type Action = {
  id: string;

  action_type: string;

  title: string;

  description: string;

  status: string;

  assigned_to:
    string | null;

  due_date:
    string | null;

  project_id: string;
};

export default function ActionsPage() {

  const {
    profile,
  } = useAuth();

  const [
    actions,
    setActions
  ] = useState<Action[]>([]);

  const [
    loading,
    setLoading
  ] = useState(true);

  const [
    assigningActionId,
    setAssigningActionId
  ] = useState<
    string | null
  >(null);

  useEffect(() => {

    loadActions();

  }, []);

  async function loadActions() {

    try {

      const response =
        await apiFetch("/actions/open");

      const data =
        await response.json();

      setActions(data);

    } catch (error) {

      console.error(error);

    } finally {

      setLoading(false);
    }
  }

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

      case "IN_PROGRESS":
        return "בתהליך";

      case "BLOCKED":
        return "חסום";

      case "ESCALATED":
        return "הוסלם";

      case "COMPLETED":
        return "הושלם";

      default:
        return status;
    }
  }

  async function updateActionStatus(
    actionId: string,
    status: string,
  ) {
    const endpointByStatus: Record<string, string> = {
      IN_PROGRESS: "start",
      COMPLETED: "complete",
      BLOCKED: "block",
      ESCALATED: "escalate",
      CLOSED: "close",
    };

    const endpoint = endpointByStatus[status];

    if (!endpoint) {
      return;
    }

    try {
      await apiFetch(
        `/actions/${actionId}/${endpoint}`,
        { method: "POST" }
      );

      await loadActions();
    } catch (error) {
      console.error(error);
    }
  }

  async function assignAction(
    actionId: string,
  ) {

    const assignedTo =
      prompt(
        "הכנס שם אחראי"
      );

    if (!assignedTo) {
      return;
    }

    try {

      setAssigningActionId(
        actionId
      );

      await apiFetch(
        `/actions/${actionId}/assign`,
        {
          method: "POST",
          body: JSON.stringify({
            assigned_to: assignedTo,
          }),
        }
      );

      await loadActions();

    } catch (error) {

      console.error(error);

    } finally {

      setAssigningActionId(
        null
      );
    }
  }

  return (

    <main dir="rtl" className="of-dashboard-page">

      <div className="mx-auto max-w-6xl">

        {/* HEADER */}

        <div className="mb-10">

          <h1 className="of-page-title">
            פעולות תפעוליות
          </h1>

          <p className="of-page-desc mt-3">
            ניהול פעולות שנוצרו על ידי מערכת AI
          </p>

        </div>

        {/* LOADING */}

        {loading && (

          <div>
            טוען פעולות...
          </div>

        )}

        {/* EMPTY */}

        {
          !loading
          && actions.length === 0
          && (

            <div className="of-card of-card-p8">
              אין פעולות פתוחות
            </div>

          )
        }

        {/* ACTIONS */}

        <div className="grid gap-6">

          {actions.map(
            (action) => (

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
                    gap-6
                    flex-wrap
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
                    {
                      getStatusLabel(
                        action.status
                      )
                    }
                  </Badge>

                </div>

                {/* BODY */}

                <div className="space-y-4">

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
                      {
                        getActionTypeLabel(
                          action.action_type
                        )
                      }
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
                      "
                    >
                      {
                        action.description
                      }
                    </p>

                  </div>

                  <div>

                    <h3
                      className="
                        font-semibold
                        mb-2
                      "
                    >
                      אחראי
                    </h3>

                    <p>
                      {
                        action.assigned_to
                        || "לא הוגדר"
                      }
                    </p>

                  </div>

                </div>

                {/* ACTIONS */}

                <div
                  className="
                    flex
                    gap-3
                    flex-wrap
                    mt-8
                  "
                >

                  <Link
                    href={`/actions/${action.id}`}
                    className="
                      px-5
                      py-3
                      rounded-2xl
                      border
                      border-zinc-200
                      dark:border-zinc-700
                      hover:bg-zinc-100
                      dark:hover:bg-zinc-800
                      transition
                    "
                  >
                    פתח Workspace
                  </Link>

                  {
                    canManageActions(
                      profile?.role
                    )
                    && (

                      <button
                        onClick={() =>
                          assignAction(
                            action.id
                          )
                        }
                        disabled={
                          assigningActionId
                          === action.id
                        }
                        className="
                          px-5
                          py-3
                          rounded-2xl
                          bg-indigo-600
                          text-white
                          hover:bg-indigo-700
                          transition
                        "
                      >

                        {
                          assigningActionId
                          === action.id

                            ? "משייך..."

                            : (
                              action.assigned_to

                                ? "שנה אחראי"

                                : "שייך פעולה"
                            )
                        }

                      </button>

                    )
                  }

                  {
                    canManageActions(
                      profile?.role
                    )
                    && (

                      <>
                        <button
                          onClick={() =>
                            updateActionStatus(
                              action.id,
                              "IN_PROGRESS"
                            )
                          }
                          className="
                            px-5
                            py-3
                            rounded-2xl
                            bg-yellow-500
                            text-white
                            hover:bg-yellow-600
                            transition
                          "
                        >
                          התחל טיפול
                        </button>

                        <button
                          onClick={() =>
                            updateActionStatus(
                              action.id,
                              "COMPLETED"
                            )
                          }
                          className="
                            px-5
                            py-3
                            rounded-2xl
                            bg-green-600
                            text-white
                            hover:bg-green-700
                            transition
                          "
                        >
                          סיים פעולה
                        </button>

                      </>

                    )
                  }

                  {
                    canEscalateActions(
                      profile?.role
                    )
                    && (

                      <button
                        onClick={() =>
                          updateActionStatus(
                            action.id,
                            "ESCALATED"
                          )
                        }
                        className="
                          px-5
                          py-3
                          rounded-2xl
                          bg-red-600
                          text-white
                          hover:bg-red-700
                          transition
                        "
                      >
                        הסלם
                      </button>

                    )
                  }

                </div>

              </div>

            )
          )}

        </div>

      </div>

    </main>
  );
}