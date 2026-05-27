"use client";

import Link from "next/link";

import {
  useEffect,
  useState,
} from "react";

import {
  useAuth,
} from "@/contexts/AuthContext";

import {
  canManageActions,
  canEscalateActions,
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
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/actions/open`
        );

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

    try {

      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/actions/${actionId}/status`,
        {

          method: "PATCH",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            status,
          }),
        }
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

      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/actions/${actionId}/assign`,
        {

          method: "PATCH",

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

    <main
      dir="rtl"
      className="
        bg-zinc-100
        dark:bg-zinc-950
        text-zinc-900
        dark:text-zinc-100
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

          )
        }

        {/* ACTIONS */}

        <div className="grid gap-6">

          {actions.map(
            (action) => (

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
                    {
                      getStatusLabel(
                        action.status
                      )
                    }
                  </div>

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