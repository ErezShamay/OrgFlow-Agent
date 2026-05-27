"use client";

// @ts-ignore: allow implicit any for react in this file; add @types/react to the project to fix properly
import {
  useEffect,
  useState,
} from "react";

type AIExecutionLog = {
  id: string;
  project_id?: string | null;
  execution_type: string;
  status: string;
  failure_type?: string | null;
  severity?: string | null;
  retry_count?: number;
  last_retry_at?: string | null;
  next_retry_at?: string | null;
  dead_lettered?: boolean;
  recovery_locked?: boolean;
  created_at?: string | null;
  details?: Record<string, unknown> | null;
};

type AIRecoveryResponse = {
  dead_letters: AIExecutionLog[];
  dead_letter_count: number;
};

declare const process: {
  env: {
    NEXT_PUBLIC_API_URL?: string;
  };
};

export default function DeadLettersPage() {
  const [
    deadLetters,
    setDeadLetters,
  ] = useState<AIExecutionLog[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  useEffect(() => {
    loadDeadLetters();
  }, []);

  async function loadDeadLetters() {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/automation/ai-recovery`
      );

      if (!response.ok) {
        throw new Error(
          "Failed loading dead letters"
        );
      }

      const data: AIRecoveryResponse =
        await response.json();

      setDeadLetters(
        data.dead_letters || []
      );

    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <main className="p-10">
        טוען Dead Letter Dashboard...
      </main>
    );
  }

  return (
    <main
      className="
        p-10
        bg-zinc-100
        dark:bg-zinc-950
        min-h-screen
        text-zinc-900
        dark:text-zinc-100
      "
    >
      <div className="mb-10">
        <h1 className="text-5xl font-black">
          Dead Letter Dashboard
        </h1>

        <p
          className="
            mt-4
            text-xl
            text-zinc-600
            dark:text-zinc-400
          "
        >
          ניטור תהליכי AI שנכשלו ולא ניתנים לשחזור אוטומטי
        </p>
      </div>

      <div
        className="
          grid
          grid-cols-1
          md:grid-cols-3
          gap-6
          mb-10
        "
      >
        <MetricCard
          title="Dead Letters"
          value={String(deadLetters.length)}
        />

        <MetricCard
          title="Critical"
          value={String(
            deadLetters.filter(
              item => item.severity === "HIGH"
            ).length
          )}
        />

        <MetricCard
          title="Locked"
          value={String(
            deadLetters.filter(
              item => item.recovery_locked
            ).length
          )}
        />
      </div>

      <div className="grid gap-6">
        {deadLetters.map((item) => (
          <div
            key={item.id}
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
                <h2 className="text-2xl font-black">
                  {item.execution_type}
                </h2>

                <p
                  className="
                    mt-2
                    text-sm
                    text-zinc-500
                    break-all
                  "
                >
                  {item.id}
                </p>
              </div>

              <StatusBadge status={item.status} />
            </div>

            <div
              className="
                grid
                grid-cols-1
                md:grid-cols-2
                xl:grid-cols-4
                gap-6
                mt-8
              "
            >
              <InfoCard
                title="Failure Type"
                value={item.failure_type || "-"}
              />

              <InfoCard
                title="Severity"
                value={item.severity || "-"}
              />

              <InfoCard
                title="Retries"
                value={String(item.retry_count || 0)}
              />

              <InfoCard
                title="Recovery Locked"
                value={item.recovery_locked ? "Yes" : "No"}
              />

              <InfoCard
                title="Project ID"
                value={item.project_id || "-"}
              />

              <InfoCard
                title="Created At"
                value={
                  item.created_at
                    ? new Date(item.created_at).toLocaleString("he-IL")
                    : "-"
                }
              />

              <InfoCard
                title="Last Retry"
                value={
                  item.last_retry_at
                    ? new Date(item.last_retry_at).toLocaleString("he-IL")
                    : "-"
                }
              />

              <InfoCard
                title="Next Retry"
                value={
                  item.next_retry_at
                    ? new Date(item.next_retry_at).toLocaleString("he-IL")
                    : "-"
                }
              />
            </div>

            <div className="mt-8">
              <h3 className="font-bold mb-3">
                Details
              </h3>

              <pre
                className="
                  bg-zinc-100
                  dark:bg-zinc-950
                  border
                  border-zinc-200
                  dark:border-zinc-800
                  rounded-2xl
                  p-5
                  overflow-auto
                  text-sm
                  direction-ltr
                  text-left
                "
              >
                {JSON.stringify(
                  item.details || {},
                  null,
                  2
                )}
              </pre>
            </div>
          </div>
        ))}

        {deadLetters.length === 0 && (
          <div
            className="
              bg-white
              dark:bg-zinc-900
              border
              border-zinc-200
              dark:border-zinc-800
              rounded-3xl
              p-10
              text-zinc-500
            "
          >
            אין כרגע Dead Letters.
          </div>
        )}
      </div>
    </main>
  );
}

function MetricCard({
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
        rounded-3xl
        p-7
      "
    >
      <p className="text-zinc-500 mb-3">
        {title}
      </p>

      <h3 className="text-4xl font-black">
        {value}
      </h3>
    </div>
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
    <div>
      <p className="text-zinc-500 mb-2">
        {title}
      </p>

      <p className="font-bold break-all">
        {value}
      </p>
    </div>
  );
}

function StatusBadge({
  status,
}: {
  status: string;
}) {
  const styles = {
    DEAD_LETTERED:
      "bg-red-100 text-red-700",
    FAILED:
      "bg-red-100 text-red-700",
    RECOVERED:
      "bg-green-100 text-green-700",
    SKIPPED:
      "bg-zinc-100 text-zinc-700",
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
          ] || "bg-zinc-100 text-zinc-700"
        }
      `}
    >
      {status}
    </span>
  );
}