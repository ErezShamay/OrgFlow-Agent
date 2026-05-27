"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  useParams,
} from "next/navigation";

import {
  useRealtime,
} from "@/hooks/useRealtime";

type TimelineItem = {
  id: string;

  activity_type: string;

  title: string;

  description: string;

  created_at: string;
};

type Comment = {
  id: string;

  comment: string;

  created_by: string;

  created_at: string;
};

type ActionDetailsResponse = {

  success: boolean;

  action: {
    id: string;

    title: string;

    description: string;

    status: string;

    action_type: string;

    assigned_to: string | null;

    due_date: string | null;

    priority: string;

    created_at: string;
  };

  timeline: TimelineItem[];

  sla: {

    due_date: string | null;

    is_overdue: boolean;
  };

  assignment: {

    assigned_to: string | null;
  };
};

export default function ActionDetailsPage() {

  const params = useParams();

  const actionId =
    params.id as string;

  const [
    data,
    setData
  ] = useState<
    ActionDetailsResponse | null
  >(null);

  const [
    comments,
    setComments
  ] = useState<Comment[]>([]);

  const [
    newComment,
    setNewComment
  ] = useState("");

  const [
    loading,
    setLoading
  ] = useState(true);

  const [
    submitting,
    setSubmitting
  ] = useState(false);

  useEffect(() => {

    loadAction();

    loadComments();

  }, []);

  // ==========================================
  // REALTIME
  // ==========================================

  useRealtime({

    channelName:
      `comments-${actionId}`,

    table:
      "action_comments",

    onChange: () => {

      loadComments();
    },
  });

  useRealtime({

    channelName:
      `timeline-${actionId}`,

    table:
      "workspace_activities",

    onChange: () => {

      loadAction();
    },
  });

  async function loadAction() {

    try {

      const response =
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/actions/${actionId}`
        );

      if (!response.ok) {

        throw new Error(
          "Failed loading action"
        );
      }

      const result =
        await response.json();

      setData(result);

    } catch (error) {

      console.error(error);

    } finally {

      setLoading(false);
    }
  }

  async function loadComments() {

    try {

      const response =
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/actions/${actionId}/comments`
        );

      if (!response.ok) {

        throw new Error(
          "Failed loading comments"
        );
      }

      const result =
        await response.json();

      setComments(result);

    } catch (error) {

      console.error(error);
    }
  }

  async function submitComment() {

    if (!newComment.trim()) {
      return;
    }

    try {

      setSubmitting(true);

      const response =
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/actions/${actionId}/comments`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({

              comment:
                newComment,

              created_by:
                "ארז שמאי",
            }),
          }
        );

      if (!response.ok) {

        throw new Error(
          "Failed creating comment"
        );
      }

      setNewComment("");

      await loadComments();

    } catch (error) {

      console.error(error);

    } finally {

      setSubmitting(false);
    }
  }

  if (loading) {

    return (
      <main className="p-10">
        טוען פעולה...
      </main>
    );
  }

  if (
    !data
    || !data.success
  ) {

    return (
      <main className="p-10">
        פעולה לא נמצאה
      </main>
    );
  }

  const action =
    data.action;

  return (

    <main
      className="
        p-10
        text-zinc-900
        dark:text-zinc-100
      "
    >

      {/* HEADER */}

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

        <div
          className="
            flex
            justify-between
            items-start
            gap-6
            flex-wrap
          "
        >

          <div>

            <p
              className="
                text-zinc-500
                mb-3
              "
            >
              Operational Action
            </p>

            <h1
              className="
                text-4xl
                font-black
              "
            >
              {action.title}
            </h1>

            <p
              className="
                mt-5
                text-lg
                text-zinc-600
                dark:text-zinc-400
                leading-8
              "
            >
              {action.description}
            </p>

          </div>

          <StatusBadge
            status={action.status}
          />

        </div>

      </div>

      {/* METADATA */}

      <div
        className="
          grid
          grid-cols-1
          md:grid-cols-2
          xl:grid-cols-4
          gap-6
          mt-10
        "
      >

        <InfoCard
          title="סוג פעולה"
          value={action.action_type}
        />

        <InfoCard
          title="עדיפות"
          value={action.priority}
        />

        <InfoCard
          title="אחראי"
          value={
            action.assigned_to
            || "לא משויך"
          }
        />

        <InfoCard
          title="תאריך יעד"
          value={
            action.due_date
              ? new Date(
                  action.due_date
                ).toLocaleDateString(
                  "he-IL"
                )
              : "ללא יעד"
          }
        />

      </div>

      {/* SLA */}

      <div
        className="
          mt-10
          border
          rounded-3xl
          p-8
        "
      >

        <div
          className="
            flex
            justify-between
            items-center
            flex-wrap
            gap-4
          "
        >

          <div>

            <h2
              className="
                text-2xl
                font-bold
              "
            >
              SLA Status
            </h2>

            <p
              className="
                mt-3
                text-lg
              "
            >

              {
                data.sla.is_overdue

                  ? "הפעולה חרגה מהיעד"

                  : "הפעולה עומדת ב-SLA"
              }

            </p>

          </div>

          <div>

            {
              data.sla.is_overdue

                ? (
                  <span
                    className="
                      px-4
                      py-2
                      rounded-full
                      bg-red-600
                      text-white
                      font-semibold
                    "
                  >
                    OVERDUE
                  </span>
                )

                : (
                  <span
                    className="
                      px-4
                      py-2
                      rounded-full
                      bg-green-600
                      text-white
                      font-semibold
                    "
                  >
                    HEALTHY
                  </span>
                )
            }

          </div>

        </div>

      </div>

      {/* COMMENTS */}

      <div className="mt-10">

        <h2
          className="
            text-3xl
            font-bold
            mb-6
          "
        >
          הערות תפעוליות
        </h2>

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

          <textarea
            value={newComment}
            onChange={(e) =>
              setNewComment(
                e.target.value
              )
            }
            placeholder="הוסף הערה תפעולית..."
            className="
              w-full
              min-h-[120px]
              rounded-2xl
              border
              border-zinc-200
              dark:border-zinc-700
              bg-transparent
              p-4
              outline-none
            "
          />

          <button
            onClick={submitComment}
            disabled={submitting}
            className="
              mt-4
              px-6
              py-3
              rounded-2xl
              bg-blue-600
              text-white
              font-semibold
              hover:bg-blue-700
              transition
            "
          >
            {
              submitting

                ? "שומר..."

                : "הוסף הערה"
            }
          </button>

        </div>

        <div className="grid gap-5 mt-6">

          {comments.map(
            comment => (

              <div
                key={comment.id}
                className="
                  bg-white
                  dark:bg-zinc-900
                  border
                  border-zinc-200
                  dark:border-zinc-800
                  rounded-2xl
                  p-6
                "
              >

                <div
                  className="
                    flex
                    justify-between
                    items-center
                    gap-4
                    flex-wrap
                    mb-4
                  "
                >

                  <h3
                    className="
                      font-bold
                    "
                  >
                    {
                      comment.created_by
                    }
                  </h3>

                  <span
                    className="
                      text-sm
                      text-zinc-500
                    "
                  >
                    {
                      new Date(
                        comment.created_at
                      ).toLocaleString(
                        "he-IL"
                      )
                    }
                  </span>

                </div>

                <p
                  className="
                    leading-8
                    text-zinc-700
                    dark:text-zinc-300
                  "
                >
                  {comment.comment}
                </p>

              </div>

            )
          )}

        </div>

      </div>

      {/* TIMELINE */}

      <div className="mt-10">

        <h2
          className="
            text-3xl
            font-bold
            mb-6
          "
        >
          Timeline
        </h2>

        <div className="grid gap-5">

          {data.timeline.map(
            activity => (

              <div
                key={activity.id}
                className="
                  bg-white
                  dark:bg-zinc-900
                  border
                  border-zinc-200
                  dark:border-zinc-800
                  rounded-2xl
                  p-6
                "
              >

                <div
                  className="
                    flex
                    justify-between
                    items-start
                    gap-4
                    flex-wrap
                  "
                >

                  <div>

                    <h3
                      className="
                        text-lg
                        font-bold
                      "
                    >
                      {activity.title}
                    </h3>

                    <p
                      className="
                        mt-3
                        text-zinc-600
                        dark:text-zinc-400
                        leading-7
                      "
                    >
                      {
                        activity.description
                      }
                    </p>

                  </div>

                  <span
                    className="
                      text-sm
                      text-zinc-500
                    "
                  >
                    {
                      new Date(
                        activity.created_at
                      ).toLocaleString(
                        "he-IL"
                      )
                    }
                  </span>

                </div>

              </div>

            )
          )}

        </div>

      </div>

    </main>
  );
}

function InfoCard({
  title,
  value,
}: {
  title: string;
  value: string;
}) {

  return (

    <div
      className="
        bg-white
        dark:bg-zinc-900
        border
        border-zinc-200
        dark:border-zinc-800
        rounded-2xl
        p-6
      "
    >

      <p
        className="
          text-zinc-500
          mb-3
        "
      >
        {title}
      </p>

      <h3
        className="
          text-xl
          font-bold
        "
      >
        {value}
      </h3>

    </div>

  );
}

function StatusBadge({
  status,
}: {
  status: string;
}) {

  const styles = {

    OPEN:
      "bg-blue-100 text-blue-700",

    IN_PROGRESS:
      "bg-yellow-100 text-yellow-700",

    BLOCKED:
      "bg-orange-100 text-orange-700",

    ESCALATED:
      "bg-red-100 text-red-700",

    COMPLETED:
      "bg-green-100 text-green-700",
  };

  return (

    <span
      className={`
        px-4
        py-2
        rounded-full
        font-semibold

        ${
          styles[
            status as keyof typeof styles
          ]
          || "bg-zinc-100 text-zinc-700"
        }
      `}
    >
      {status}
    </span>

  );
}