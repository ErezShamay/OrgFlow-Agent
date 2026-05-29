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
  replayable?: boolean;
  created_at?: string | null;
  details?: Record<string, unknown> | null;
};

type RecoveryDashboard = {
  dead_letters: AIExecutionLog[];
  dead_letter_count: number;
  metrics: {
    dead_letter_count: number;
    by_failure_type: Record<string, number>;
    by_severity: Record<string, number>;
    replay_summary: {
      total_replays: number;
      completed: number;
      failed: number;
    };
  };
  analytics: {
    locked_count: number;
    high_severity_count: number;
    replayable_count: number;
  };
};

declare const process: {
  env: {
    NEXT_PUBLIC_API_URL?: string;
  };
};

export default function DeadLettersPage() {
  const [dashboard, setDashboard] = useState<RecoveryDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLogId, setActionLogId] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    query: "",
    execution_type: "",
    failure_type: "",
    severity: "",
  });

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.query) params.set("query", filters.query);
      if (filters.execution_type) {
        params.set("execution_type", filters.execution_type);
      }
      if (filters.failure_type) {
        params.set("failure_type", filters.failure_type);
      }
      if (filters.severity) params.set("severity", filters.severity);

      const queryString = params.toString();
      const url = queryString
        ? `${process.env.NEXT_PUBLIC_API_URL}/automation/dead-letters?${queryString}`
        : `${process.env.NEXT_PUBLIC_API_URL}/automation/dead-letters/dashboard`;

      const response = await fetch(url);

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
            by_failure_type: {},
            by_severity: {},
            replay_summary: {
              total_replays: 0,
              completed: 0,
              failed: 0,
            },
          },
          analytics: {
            locked_count: 0,
            high_severity_count: 0,
            replayable_count: data.dead_letters.length,
          },
        });
      } else {
        setDashboard(data);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  async function retryDeadLetter(logId: string) {
    setActionLogId(logId);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/automation/dead-letters/${logId}/retry`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ initiated_by: "dashboard-operator" }),
        }
      );
      if (!response.ok) {
        throw new Error("Retry failed");
      }
      await loadDashboard();
    } catch (error) {
      console.error(error);
    } finally {
      setActionLogId(null);
    }
  }

  async function manualRecover(logId: string) {
    setActionLogId(logId);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/automation/dead-letters/${logId}/manual-recover`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ initiated_by: "dashboard-operator" }),
        }
      );
      if (!response.ok) {
        throw new Error("Manual recovery failed");
      }
      await loadDashboard();
    } catch (error) {
      console.error(error);
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
          ניטור, סינון ושחזור תהליכי AI שנכשלו
        </p>
      </div>

      <div
        className="
          bg-white
          dark:bg-zinc-900
          border
          border-zinc-200
          dark:border-zinc-800
          rounded-3xl
          p-6
          mb-10
          grid
          grid-cols-1
          md:grid-cols-4
          gap-4
        "
      >
        <input
          className="border rounded-xl px-4 py-3 dark:bg-zinc-950"
          placeholder="חיפוש..."
          value={filters.query}
          onChange={(event) =>
            setFilters({ ...filters, query: event.target.value })
          }
        />
        <input
          className="border rounded-xl px-4 py-3 dark:bg-zinc-950"
          placeholder="Execution Type"
          value={filters.execution_type}
          onChange={(event) =>
            setFilters({ ...filters, execution_type: event.target.value })
          }
        />
        <input
          className="border rounded-xl px-4 py-3 dark:bg-zinc-950"
          placeholder="Failure Type"
          value={filters.failure_type}
          onChange={(event) =>
            setFilters({ ...filters, failure_type: event.target.value })
          }
        />
        <button
          className="bg-black text-white dark:bg-white dark:text-black rounded-xl font-bold"
          onClick={loadDashboard}
        >
          סנן / רענן
        </button>
      </div>

      <div
        className="
          grid
          grid-cols-1
          md:grid-cols-4
          gap-6
          mb-10
        "
      >
        <MetricCard
          title="Dead Letters"
          value={String(dashboard?.dead_letter_count || 0)}
        />
        <MetricCard
          title="High Severity"
          value={String(dashboard?.analytics?.high_severity_count || 0)}
        />
        <MetricCard
          title="Replayable"
          value={String(dashboard?.analytics?.replayable_count || 0)}
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
                <p className="mt-2 text-sm text-zinc-500 break-all">
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
              <InfoCard title="Failure Type" value={item.failure_type || "-"} />
              <InfoCard title="Severity" value={item.severity || "-"} />
              <InfoCard title="Retries" value={String(item.retry_count || 0)} />
              <InfoCard
                title="Replayable"
                value={item.replayable === false ? "No" : "Yes"}
              />
            </div>

            <div className="mt-8 flex gap-4 flex-wrap">
              <button
                disabled={actionLogId === item.id}
                onClick={() => retryDeadLetter(item.id)}
                className="px-5 py-3 rounded-xl bg-blue-600 text-white font-bold disabled:opacity-50"
              >
                {actionLogId === item.id ? "מבצע..." : "Retry"}
              </button>
              <button
                disabled={actionLogId === item.id}
                onClick={() => manualRecover(item.id)}
                className="px-5 py-3 rounded-xl bg-emerald-600 text-white font-bold disabled:opacity-50"
              >
                Manual Recover
              </button>
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
      <p className="text-zinc-500 mb-3">{title}</p>
      <h3 className="text-4xl font-black">{value}</h3>
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
      <p className="text-zinc-500 mb-2">{title}</p>
      <p className="font-bold break-all">{value}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    DEAD_LETTERED: "bg-red-100 text-red-700",
    FAILED: "bg-red-100 text-red-700",
    RECOVERED: "bg-green-100 text-green-700",
    SKIPPED: "bg-zinc-100 text-zinc-700",
  };

  return (
    <span
      className={`
        px-4 py-2 rounded-full font-semibold
        ${styles[status] || "bg-zinc-100 text-zinc-700"}
      `}
    >
      {status}
    </span>
  );
}
