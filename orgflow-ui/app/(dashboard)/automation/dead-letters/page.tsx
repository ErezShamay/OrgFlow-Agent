"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api/client";
import { showToast } from "@/lib/ui/toast";

type AIExecutionLog = {
  id: string;
  project_id?: string | null;
  execution_type: string;
  status: string;
  failure_type?: string | null;
  severity?: string | null;
  retry_count?: number;
  replayable?: boolean;
};

type RecoveryDashboard = {
  dead_letters: AIExecutionLog[];
  dead_letter_count: number;
  metrics: {
    dead_letter_count: number;
    replay_summary: {
      completed: number;
    };
  };
  analytics: {
    high_severity_count: number;
    replayable_count: number;
  };
};

export default function DeadLettersPage() {
  const [dashboard, setDashboard] =
    useState<RecoveryDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLogId, setActionLogId] =
    useState<string | null>(null);
  const [filters, setFilters] = useState({
    query: "",
    execution_type: "",
    failure_type: "",
  });

  useEffect(() => {
    void loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      setLoading(true);
      const params = new URLSearchParams();

      if (filters.query) {
        params.set("query", filters.query);
      }

      if (filters.execution_type) {
        params.set("execution_type", filters.execution_type);
      }

      if (filters.failure_type) {
        params.set("failure_type", filters.failure_type);
      }

      const queryString = params.toString();
      const path = queryString
        ? `/automation/dead-letters?${queryString}`
        : "/automation/dead-letters/dashboard";

      const response = await apiFetch(path);

      if (!response.ok) {
        throw new Error("Failed loading dead letters");
      }

      const data = await response.json();

      if (data.dead_letters && !data.metrics) {
        setDashboard({
          dead_letters: data.dead_letters,
          dead_letter_count: data.dead_letters.length,
          metrics: {
            dead_letter_count: data.dead_letters.length,
            replay_summary: { completed: 0 },
          },
          analytics: {
            high_severity_count: 0,
            replayable_count: data.dead_letters.length,
          },
        });
      } else {
        setDashboard(data);
      }
    } catch (error) {
      console.error(error);
      showToast("שגיאה בטעינת Dead Letters", "error");
    } finally {
      setLoading(false);
    }
  }

  async function retryDeadLetter(logId: string) {
    setActionLogId(logId);

    try {
      const response = await apiFetch(
        `/automation/dead-letters/${logId}/retry`,
        {
          method: "POST",
          body: JSON.stringify({
            initiated_by: "dashboard-operator",
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Retry failed");
      }

      showToast("Retry בוצע בהצלחה", "success");
      await loadDashboard();
    } catch (error) {
      console.error(error);
      showToast("שגיאה ב-Retry", "error");
    } finally {
      setActionLogId(null);
    }
  }

  async function replayDeadLetter(logId: string) {
    setActionLogId(logId);

    try {
      const response = await apiFetch(
        `/automation/dead-letters/${logId}/replay`,
        {
          method: "POST",
          body: JSON.stringify({
            initiated_by: "dashboard-operator",
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Replay failed");
      }

      showToast("Replay בוצע בהצלחה", "success");
      await loadDashboard();
    } catch (error) {
      console.error(error);
      showToast("שגיאה ב-Replay", "error");
    } finally {
      setActionLogId(null);
    }
  }

  async function manualRecover(logId: string) {
    setActionLogId(logId);

    try {
      const response = await apiFetch(
        `/automation/dead-letters/${logId}/manual-recover`,
        {
          method: "POST",
          body: JSON.stringify({
            initiated_by: "dashboard-operator",
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Manual recovery failed");
      }

      showToast("שחזור ידני הושלם", "success");
      await loadDashboard();
    } catch (error) {
      console.error(error);
      showToast("שגיאה בשחזור ידני", "error");
    } finally {
      setActionLogId(null);
    }
  }

  const deadLetters = dashboard?.dead_letters || [];

  if (loading && !dashboard) {
    return (
      <main className="p-10">
        טוען Dead Letter Dashboard...
      </main>
    );
  }

  return (
    <main className="min-h-screen p-10 text-zinc-900 dark:text-zinc-100">
      <div className="mb-10">
        <h1 className="text-5xl font-black">
          Dead Letter Dashboard
        </h1>
        <p className="mt-4 text-xl text-zinc-600 dark:text-zinc-400">
          ניטור, סינון ושחזור תהליכי AI שנכשלו
        </p>
      </div>

      <div
        className="
          mb-10
          grid
          grid-cols-1
          gap-4
          rounded-3xl
          border
          border-zinc-200
          bg-white
          p-6
          dark:border-zinc-800
          dark:bg-zinc-900
          md:grid-cols-4
        "
      >
        <input
          className="rounded-xl border px-4 py-3 dark:bg-zinc-950"
          placeholder="חיפוש..."
          value={filters.query}
          onChange={(event) =>
            setFilters({
              ...filters,
              query: event.target.value,
            })
          }
        />
        <input
          className="rounded-xl border px-4 py-3 dark:bg-zinc-950"
          placeholder="Execution Type"
          value={filters.execution_type}
          onChange={(event) =>
            setFilters({
              ...filters,
              execution_type: event.target.value,
            })
          }
        />
        <input
          className="rounded-xl border px-4 py-3 dark:bg-zinc-950"
          placeholder="Failure Type"
          value={filters.failure_type}
          onChange={(event) =>
            setFilters({
              ...filters,
              failure_type: event.target.value,
            })
          }
        />
        <button
          className="
            rounded-xl
            bg-black
            font-bold
            text-white
            dark:bg-white
            dark:text-black
          "
          onClick={() => {
            void loadDashboard();
          }}
        >
          סנן / רענן
        </button>
      </div>

      <div className="mb-10 grid grid-cols-1 gap-6 md:grid-cols-4">
        <MetricCard
          title="Dead Letters"
          value={String(dashboard?.dead_letter_count || 0)}
        />
        <MetricCard
          title="High Severity"
          value={String(
            dashboard?.analytics?.high_severity_count || 0
          )}
        />
        <MetricCard
          title="Replayable"
          value={String(
            dashboard?.analytics?.replayable_count || 0
          )}
        />
        <MetricCard
          title="Replays Completed"
          value={String(
            dashboard?.metrics?.replay_summary?.completed || 0
          )}
        />
      </div>

      <div className="grid gap-6">
        {deadLetters.map((item) => (
          <div
            key={item.id}
            className="
              rounded-3xl
              border
              border-zinc-200
              bg-white
              p-8
              dark:border-zinc-800
              dark:bg-zinc-900
            "
          >
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div>
                <h2 className="text-2xl font-black">
                  {item.execution_type}
                </h2>
                <p className="mt-2 break-all text-sm text-zinc-500">
                  {item.id}
                </p>
              </div>
              <StatusBadge status={item.status} />
            </div>

            <div className="mt-8 flex flex-wrap gap-4">
              <button
                disabled={actionLogId === item.id}
                onClick={() => retryDeadLetter(item.id)}
                className="
                  rounded-xl
                  bg-blue-600
                  px-5
                  py-3
                  font-bold
                  text-white
                  disabled:opacity-50
                "
              >
                Retry
              </button>
              <button
                disabled={actionLogId === item.id}
                onClick={() => replayDeadLetter(item.id)}
                className="
                  rounded-xl
                  bg-indigo-600
                  px-5
                  py-3
                  font-bold
                  text-white
                  disabled:opacity-50
                "
              >
                Replay
              </button>
              <button
                disabled={actionLogId === item.id}
                onClick={() => manualRecover(item.id)}
                className="
                  rounded-xl
                  bg-emerald-600
                  px-5
                  py-3
                  font-bold
                  text-white
                  disabled:opacity-50
                "
              >
                Manual Recover
              </button>
            </div>
          </div>
        ))}

        {deadLetters.length === 0 ? (
          <div
            className="
              rounded-3xl
              border
              border-zinc-200
              bg-white
              p-10
              text-zinc-500
              dark:border-zinc-800
              dark:bg-zinc-900
            "
          >
            אין כרגע Dead Letters.
          </div>
        ) : null}
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
        rounded-3xl
        border
        border-zinc-200
        bg-white
        p-7
        dark:border-zinc-800
        dark:bg-zinc-900
      "
    >
      <p className="mb-3 text-zinc-500">{title}</p>
      <h3 className="text-4xl font-black">{value}</h3>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    DEAD_LETTERED: "bg-red-100 text-red-700",
    FAILED: "bg-red-100 text-red-700",
    RECOVERED: "bg-green-100 text-green-700",
  };

  return (
    <span
      className={`
        rounded-full
        px-4
        py-2
        font-semibold
        ${styles[status] || "bg-zinc-100 text-zinc-700"}
      `}
    >
      {status}
    </span>
  );
}
