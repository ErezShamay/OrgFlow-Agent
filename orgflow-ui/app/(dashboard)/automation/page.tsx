"use client";

import { useCallback, useEffect, useState } from "react";

import Badge from "@/components/ui/Badge";
import { apiFetch } from "@/lib/api/client";

type AutomationStats = {

  health: string;

  total_runs: number;

  completed_runs: number;

  failed_runs: number;

  processed_count: number;

  error_count: number;
};

type AutomationRun = {

  id: string;

  job_name: string;

  started_at: string;

  completed_at: string | null;

  status: string;

  processed_count: number;

  error_count: number;
};

type CircuitBreaker = {

  breaker_key: string;

  state: string;

  failure_count: number;

  cooldown_until: string | null;
};

type AIExecutionLog = {

  id: string;

  project_id?: string | null;

  execution_type: string;

  status: string;

  confidence_score?: number | null;

  confidence_level?: string | null;

  failure_type?: string | null;

  severity?: string | null;

  retry_count?: number;

  next_retry_at?: string | null;

  dead_lettered?: boolean;

  recovery_locked?: boolean;

  created_at?: string | null;
};

type AIRecoveryMonitoring = {

  recent_executions: AIExecutionLog[];

  recovery_queue: AIExecutionLog[];

  dead_letters: AIExecutionLog[];

  recent_count: number;

  recovery_queue_count: number;

  dead_letter_count: number;
};

type AIExecutionLogsSummary = {

  total: number;

  successful: number;

  failed: number;

  recovered: number;

  skipped: number;

  dead_lettered: number;

  classification_rate: number | null;

  success_rate: number | null;
};

type AIExecutionLogsDashboard = {

  summary: AIExecutionLogsSummary;

  status_counts: Record<string, number>;

  execution_type_counts: Record<string, number>;

  failure_type_counts: Record<string, number>;

  severity_counts: Record<string, number>;

  recent_executions: AIExecutionLog[];
};

type AutomationHealthSummary = {

  total_runs: number;

  completed_runs: number;

  completed_with_errors: number;

  failed_runs: number;

  skipped_runs: number;

  running_runs: number;

  processed_count: number;

  error_count: number;

  success_rate: number | null;

  error_rate: number | null;
};

type JobHealth = AutomationHealthSummary & {

  job_name: string;

  health: string;

  last_status: string | null;

  last_started_at: string | null;

  last_completed_at: string | null;
};

type CircuitBreakerSummary = {

  total: number;

  open: number;

  half_open: number;

  closed: number;
};

type AIRecoverySummary = {

  recovery_queue_count: number;

  dead_letter_count: number;
};

type AutomationHealthAlert = {

  severity: string;

  title: string;

  description: string;
};

type AutomationHealthDashboard = {

  health: string;

  has_activity?: boolean;

  generated_at: string;

  summary: AutomationHealthSummary;

  job_health: JobHealth[];

  circuit_breaker_summary: CircuitBreakerSummary;

  ai_recovery_summary: AIRecoverySummary;

  alerts: AutomationHealthAlert[];
};

function formatRate(
  value: number | null | undefined,
): string {
  if (
    value === null
    || value === undefined
  ) {
    return "-";
  }

  return `${value}%`;
}

function formatHealthLabel(
  health: string,
): string {
  if (health === "NO_DATA") {
    return "אין נתונים";
  }

  return health;
}

function asList<T>(
  value: unknown,
): T[] {
  return Array.isArray(value)
    ? value
    : [];
}

export default function AutomationPage() {

  const [
    health,
    setHealth
  ] = useState<
    AutomationHealthDashboard | null
  >(null);

  const [
    stats,
    setStats
  ] = useState<
    AutomationStats | null
  >(null);

  const [
    runs,
    setRuns
  ] = useState<
    AutomationRun[]
  >([]);

  const [
    breakers,
    setBreakers
  ] = useState<
    CircuitBreaker[]
  >([]);

  const [
    recovery,
    setRecovery
  ] = useState<
    AIRecoveryMonitoring | null
  >(null);

  const [
    aiLogs,
    setAiLogs
  ] = useState<
    AIExecutionLogsDashboard | null
  >(null);

  const [
    loading,
    setLoading
  ] = useState(true);

  const loadData = useCallback(async () => {

    try {

      const [
        healthResponse,
        statsResponse,
        runsResponse,
        breakersResponse,
        recoveryResponse,
        aiLogsResponse,
      ] = await Promise.all([

        apiFetch("/automation/health"),

        apiFetch("/automation/stats"),

        apiFetch("/automation/runs"),

        apiFetch("/automation/circuit-breakers"),

        apiFetch("/automation/ai-recovery"),

        apiFetch("/automation/ai-execution-logs"),
      ]);

      const healthData =
        await healthResponse.json();

      const statsData =
        await statsResponse.json();

      const runsData =
        await runsResponse.json();

      const breakersData =
        await breakersResponse.json();

      const recoveryData =
        await recoveryResponse.json();

      const aiLogsData =
        await aiLogsResponse.json();

      setHealth(
        healthData
      );

      setStats(
        statsData
      );

      setRuns(
        asList<AutomationRun>(
          runsData
        )
      );

      setBreakers(
        asList<CircuitBreaker>(
          breakersData
        )
      );

      setRecovery(
        recoveryData
      );

      setAiLogs(
        aiLogsData
      );

    } catch (error) {

      console.error(error);

    } finally {

      setLoading(false);
    }
  }, []);

  useEffect(() => {

    const timeoutId = window.setTimeout(
      loadData,
      0
    );

    return () => {
      window.clearTimeout(
        timeoutId
      );
    };

  }, [loadData]);

  if (loading) {

    return (
      <main className="of-dashboard-page">
        טוען Automation Dashboard...
      </main>
    );
  }

  const hasOrgAutomationActivity = (
    health?.has_activity
    ?? (
      (health?.summary?.total_runs || 0) > 0
      || (aiLogs?.summary?.total || 0) > 0
      || (recovery?.recent_count || 0) > 0
    )
  );

  return (

    <main className="of-dashboard-page">

      {/* HEADER */}

      <div className="mb-10">

        <h1 className="of-page-title">
          Automation Center
        </h1>

        <p className="of-page-desc mt-4">
          ניטור אוטומציה ו-AI עבור הארגון המחובר בלבד
        </p>

      </div>

      {!hasOrgAutomationActivity && (

        <div
          className="
            of-kpi-card
            mb-10
            text-zinc-600
            dark:text-zinc-400
          "
        >
          אין עדיין פעילות אוטומציה או AI עבור הארגון הזה.
          רענן סיכום תפעולי בפרויקט כדי לייצר ריצות AI חדשות.
        </div>

      )}

      {/* HEALTH DASHBOARD */}

      <section className="mb-12">

        <div
          className="
            grid
            grid-cols-1
            xl:grid-cols-[1.2fr_2fr]
            gap-6
          "
        >

          <div
            className="of-kpi-card"
          >

            <p
              className="
                text-sm
                font-bold
                text-zinc-500
                mb-4
              "
            >
              Overall Health
            </p>

            <div
              className="
                flex
                items-center
                justify-between
                gap-4
                flex-wrap
              "
            >

              <h2
                className="
                  text-4xl
                  font-black
                "
              >
                {formatHealthLabel(
                  health?.health || "UNKNOWN"
                )}
              </h2>

              <HealthBadge
                health={
                  health?.health || "UNKNOWN"
                }
              />

            </div>

            <div
              className="
                grid
                grid-cols-2
                gap-4
                mt-8
              "
            >

              <InfoCard
                title="Success Rate"
                value={
                  formatRate(
                    health?.summary?.success_rate
                  )
                }
              />

              <InfoCard
                title="Error Rate"
                value={
                  formatRate(
                    health?.summary?.error_rate
                  )
                }
              />

              <InfoCard
                title="Running"
                value={
                  String(
                    health?.summary?.running_runs || 0
                  )
                }
              />

              <InfoCard
                title="Skipped"
                value={
                  String(
                    health?.summary?.skipped_runs || 0
                  )
                }
              />

            </div>

            <p
              className="
                mt-6
                text-sm
                text-zinc-500
              "
            >
              Updated: {
                health?.generated_at
                  ? new Date(
                      health.generated_at
                    ).toLocaleString(
                      "he-IL"
                    )
                  : "-"
              }
            </p>

          </div>

          <div
            className="
              grid
              grid-cols-1
              md:grid-cols-2
              gap-6
            "
          >

            <MetricCard
              title="Completed With Errors"
              value={
                String(
                  health?.summary?.completed_with_errors || 0
                )
              }
            />

            <MetricCard
              title="Failed Runs"
              value={
                String(
                  health?.summary?.failed_runs || 0
                )
              }
            />

            <MetricCard
              title="Open Breakers"
              value={
                String(
                  health?.circuit_breaker_summary?.open || 0
                )
              }
            />

            <MetricCard
              title="Recovery Queue"
              value={
                String(
                  health?.ai_recovery_summary?.recovery_queue_count || 0
                )
              }
            />

          </div>

        </div>

        <div
          className="
            grid
            grid-cols-1
            xl:grid-cols-[2fr_1fr]
            gap-6
            mt-6
          "
        >

          <JobHealthTable
            jobs={
              health?.job_health || []
            }
          />

          <AlertList
            alerts={
              health?.alerts || []
            }
          />

        </div>

      </section>

      {/* AI EXECUTION LOGS */}

      <section className="mt-12">

        <h2
          className="
            text-3xl
            font-bold
            mb-6
          "
        >
          AI Execution Logs
        </h2>

        <div
          className="
            grid
            grid-cols-1
            md:grid-cols-2
            xl:grid-cols-4
            gap-6
          "
        >

          <MetricCard
            title="AI Executions"
            value={
              String(
                aiLogs?.summary?.total || 0
              )
            }
          />

          <MetricCard
            title="AI Success Rate"
            value={
              formatRate(
                aiLogs?.summary?.success_rate
              )
            }
          />

          <MetricCard
            title="Failed AI Executions"
            value={
              String(
                aiLogs?.summary?.failed || 0
              )
            }
          />

          <MetricCard
            title="Failure Classification"
            value={
              formatRate(
                aiLogs?.summary?.classification_rate
              )
            }
          />

        </div>

        <div
          className="
            grid
            grid-cols-1
            xl:grid-cols-[1fr_1fr_2fr]
            gap-6
            mt-6
          "
        >

          <DistributionPanel
            title="Status"
            items={
              aiLogs?.status_counts || {}
            }
          />

          <DistributionPanel
            title="Failure Types"
            items={
              aiLogs?.failure_type_counts || {}
            }
          />

          <AIExecutionLogTable
            executions={
              aiLogs?.recent_executions || []
            }
          />

        </div>

        <div
          className="
            grid
            grid-cols-1
            xl:grid-cols-2
            gap-6
            mt-6
          "
        >

          <DistributionPanel
            title="Execution Types"
            items={
              aiLogs?.execution_type_counts || {}
            }
          />

          <DistributionPanel
            title="Severity"
            items={
              aiLogs?.severity_counts || {}
            }
          />

        </div>

      </section>

      {/* HEALTH */}

      <div
        className="
          grid
          grid-cols-1
          md:grid-cols-2
          xl:grid-cols-5
          gap-6
          mt-12
        "
      >

        <MetricCard
          title="Automation Health"
          value={
            formatHealthLabel(
              stats?.health || "UNKNOWN"
            )
          }
        />

        <MetricCard
          title="Total Runs"
          value={
            String(
              stats?.total_runs || 0
            )
          }
        />

        <MetricCard
          title="Completed Runs"
          value={
            String(
              stats?.completed_runs || 0
            )
          }
        />

        <MetricCard
          title="Processed Actions"
          value={
            String(
              stats?.processed_count || 0
            )
          }
        />

        <MetricCard
          title="Errors"
          value={
            String(
              stats?.error_count || 0
            )
          }
        />

      </div>

      {/* AI RECOVERY */}

      <div className="mt-12">

        <h2
          className="
            text-3xl
            font-bold
            mb-6
          "
        >
          AI Recovery
        </h2>

        <div
          className="
            grid
            grid-cols-1
            md:grid-cols-3
            gap-6
          "
        >

          <MetricCard
            title="Recent AI Executions"
            value={
              String(
                recovery?.recent_count || 0
              )
            }
          />

          <MetricCard
            title="Recovery Queue"
            value={
              String(
                recovery?.recovery_queue_count || 0
              )
            }
          />

          <MetricCard
            title="Dead Letters"
            value={
              String(
                recovery?.dead_letter_count || 0
              )
            }
          />

        </div>

        <div
          className="
            grid
            grid-cols-1
            xl:grid-cols-3
            gap-5
            mt-6
          "
        >

          <ExecutionList
            title="Recovery Queue"
            emptyText="No executions waiting for recovery."
            executions={
              recovery?.recovery_queue || []
            }
          />

          <ExecutionList
            title="Dead Letter Queue"
            emptyText="No dead-lettered executions."
            executions={
              recovery?.dead_letters || []
            }
          />

          <ExecutionList
            title="Recent AI Executions"
            emptyText="No AI executions recorded yet."
            executions={
              recovery?.recent_executions || []
            }
          />

        </div>

      </div>

      {/* CIRCUIT BREAKERS */}

      <div className="mt-12">

        <h2
          className="
            text-3xl
            font-bold
            mb-6
          "
        >
          Circuit Breakers
        </h2>

        <div
          className="
            grid
            grid-cols-1
            lg:grid-cols-3
            gap-5
          "
        >

          {breakers.map(
            (breaker: CircuitBreaker) => (

              <div
                key={breaker.breaker_key}
                className="of-kpi-card"
              >

                <div
                  className="
                    flex
                    items-start
                    justify-between
                    gap-4
                  "
                >

                  <div>

                    <h3
                      className="
                        text-xl
                        font-black
                      "
                    >
                      {breaker.breaker_key}
                    </h3>

                    <p
                      className="
                        mt-2
                        text-sm
                        text-zinc-500
                      "
                    >
                      Failures: {breaker.failure_count}
                    </p>

                  </div>

                  <BreakerBadge
                    state={breaker.state}
                  />

                </div>

                <div className="mt-6">

                  <InfoCard
                    title="Cooldown Until"
                    value={
                      breaker.cooldown_until

                        ? new Date(
                            breaker.cooldown_until
                          ).toLocaleString(
                            "he-IL"
                          )

                        : "-"
                    }
                  />

                </div>

              </div>

            )
          )}

          {breakers.length === 0 && (

            <div className="of-kpi-card text-zinc-500">
              Circuit breakers הם תשתית מערכתית גלובלית
              ואינם מוצגים לפי ארגון.
            </div>
          )}

        </div>

      </div>

      {/* RUNS */}

      <div className="mt-12">

        <h2
          className="
            text-3xl
            font-bold
            mb-6
          "
        >
          Recent Automation Runs
        </h2>

        <div className="grid gap-5">

          {runs.map(
            (run: AutomationRun) => (

              <div
                key={run.id}
                className="of-card of-card-p8"
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

                    <h3
                      className="
                        text-2xl
                        font-bold
                      "
                    >
                      {run.job_name}
                    </h3>

                    <p
                      className="
                        mt-3
                        text-zinc-500
                        break-all
                      "
                    >
                      {run.id}
                    </p>

                  </div>

                  <StatusBadge
                    status={run.status}
                  />

                </div>

                <div
                  className="
                    grid
                    grid-cols-1
                    md:grid-cols-4
                    gap-6
                    mt-8
                  "
                >

                  <InfoCard
                    title="Processed"
                    value={String(
                      run.processed_count
                    )}
                  />

                  <InfoCard
                    title="Errors"
                    value={String(
                      run.error_count
                    )}
                  />

                  <InfoCard
                    title="Started"
                    value={
                      new Date(
                        run.started_at
                      ).toLocaleString(
                        "he-IL"
                      )
                    }
                  />

                  <InfoCard
                    title="Completed"
                    value={
                      run.completed_at

                        ? new Date(
                            run.completed_at
                          ).toLocaleString(
                            "he-IL"
                          )

                        : "-"
                    }
                  />

                </div>

              </div>

            )
          )}

        </div>

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

    <div className="of-kpi-card">

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
          text-4xl
          font-black
        "
      >
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

      <p
        className="
          text-zinc-500
          mb-2
        "
      >
        {title}
      </p>

      <h3
        className="
          text-lg
          font-bold
        "
      >
        {value}
      </h3>

    </div>
  );
}

function JobHealthTable({
  jobs,
}: {
  jobs: JobHealth[];
}) {

  return (

    <div
      className="of-kpi-card"
    >

      <h2
        className="
          text-2xl
          font-black
          mb-6
        "
      >
        Job Health
      </h2>

      <div className="grid gap-4">

        {jobs.map(
          (job) => (

            <div
              key={job.job_name}
              className="
                grid
                grid-cols-1
                lg:grid-cols-[1.2fr_1fr_1fr_1fr]
                gap-4
                border
                border-zinc-200
                dark:border-zinc-800
                rounded-2xl
                p-4
              "
            >

              <div className="min-w-0">

                <p
                  className="
                    font-black
                    truncate
                  "
                >
                  {job.job_name}
                </p>

                <p
                  className="
                    text-sm
                    text-zinc-500
                    mt-1
                  "
                >
                  Last: {job.last_status || "-"}
                </p>

              </div>

              <HealthBadge
                health={job.health}
              />

              <InfoCard
                title="Success"
                value={
                  formatRate(
                    job.success_rate
                  )
                }
              />

              <InfoCard
                title="Errors"
                value={
                  String(
                    job.error_count
                  )
                }
              />

            </div>

          )
        )}

        {jobs.length === 0 && (

          <p className="text-sm text-zinc-500">
            No automation jobs recorded yet.
          </p>
        )}

      </div>

    </div>
  );
}

function AlertList({
  alerts,
}: {
  alerts: AutomationHealthAlert[];
}) {

  return (

    <div
      className="of-kpi-card"
    >

      <h2
        className="
          text-2xl
          font-black
          mb-6
        "
      >
        Health Alerts
      </h2>

      <div className="grid gap-4">

        {alerts.map(
          (alert) => (

            <div
              key={`${alert.severity}-${alert.title}`}
              className="
                border
                border-zinc-200
                dark:border-zinc-800
                rounded-2xl
                p-4
              "
            >

              <div
                className="
                  flex
                  items-center
                  justify-between
                  gap-3
                "
              >

                <p className="font-bold">
                  {alert.title}
                </p>

                <StatusBadge
                  status={alert.severity}
                />

              </div>

              <p
                className="
                  text-sm
                  text-zinc-500
                  mt-3
                "
              >
                {alert.description}
              </p>

            </div>

          )
        )}

        {alerts.length === 0 && (

          <p className="text-sm text-zinc-500">
            No active automation health alerts.
          </p>
        )}

      </div>

    </div>
  );
}

function DistributionPanel({
  title,
  items,
}: {
  title: string;
  items: Record<string, number>;
}) {

  const entries = Object.entries(
    items
  ).sort(
    (first, second) => (
      second[1] - first[1]
    )
  );

  return (

    <div
      className="of-kpi-card"
    >

      <h3
        className="
          text-xl
          font-black
          mb-5
        "
      >
        {title}
      </h3>

      <div className="grid gap-3">

        {entries.map(
          ([key, value]) => (

            <div
              key={key}
              className="
                flex
                items-center
                justify-between
                gap-4
                border
                border-zinc-200
                dark:border-zinc-800
                rounded-2xl
                p-4
              "
            >

              <span
                className="
                  font-bold
                  truncate
                "
              >
                {key}
              </span>

              <span
                className="
                  text-2xl
                  font-black
                "
              >
                {value}
              </span>

            </div>
          )
        )}

        {entries.length === 0 && (

          <p className="text-sm text-zinc-500">
            No data recorded yet.
          </p>
        )}

      </div>

    </div>
  );
}

function AIExecutionLogTable({
  executions,
}: {
  executions: AIExecutionLog[];
}) {

  return (

    <div
      className="of-kpi-card"
    >

      <h3
        className="
          text-xl
          font-black
          mb-5
        "
      >
        Recent Logs
      </h3>

      <div className="grid gap-4">

        {executions.map(
          (execution) => (

            <div
              key={execution.id}
              className="
                border
                border-zinc-200
                dark:border-zinc-800
                rounded-2xl
                p-4
              "
            >

              <div
                className="
                  flex
                  items-start
                  justify-between
                  gap-4
                "
              >

                <div className="min-w-0">

                  <p
                    className="
                      font-black
                      truncate
                    "
                  >
                    {execution.execution_type}
                  </p>

                  <p
                    className="
                      text-xs
                      text-zinc-500
                      mt-1
                      break-all
                    "
                  >
                    {execution.id}
                  </p>

                </div>

                <StatusBadge
                  status={execution.status}
                />

              </div>

              <div
                className="
                  grid
                  grid-cols-2
                  lg:grid-cols-4
                  gap-4
                  mt-5
                "
              >

                <InfoCard
                  title="Confidence"
                  value={
                    execution.confidence_score !== null
                    && execution.confidence_score !== undefined
                      ? `${execution.confidence_score}`
                      : "-"
                  }
                />

                <InfoCard
                  title="Level"
                  value={
                    execution.confidence_level || "-"
                  }
                />

                <InfoCard
                  title="Failure"
                  value={
                    execution.failure_type || "-"
                  }
                />

                <InfoCard
                  title="Severity"
                  value={
                    execution.severity || "-"
                  }
                />

              </div>

            </div>
          )
        )}

        {executions.length === 0 && (

          <p className="text-sm text-zinc-500">
            No AI execution logs recorded yet.
          </p>
        )}

      </div>

    </div>
  );
}

function HealthBadge({
  health,
}: {
  health: string;
}) {
  const variantByHealth: Record<
    string,
    "success" | "warning" | "danger" | "neutral"
  > = {
    HEALTHY: "success",
    DEGRADED: "warning",
    CRITICAL: "danger",
    NO_DATA: "neutral",
    UNKNOWN: "neutral",
  };

  return (
    <Badge variant={variantByHealth[health] || "neutral"}>
      {formatHealthLabel(health)}
    </Badge>
  );
}

function ExecutionList({
  title,
  emptyText,
  executions,
}: {
  title: string;
  emptyText: string;
  executions: AIExecutionLog[];
}) {

  return (

    <div className="of-kpi-card min-h-72">

      <h3
        className="
          text-xl
          font-black
          mb-5
        "
      >
        {title}
      </h3>

      <div className="grid gap-4">

        {executions.map(
          (execution) => (

            <div
              key={execution.id}
              className="
                border
                border-zinc-200
                dark:border-zinc-800
                rounded-2xl
                p-4
              "
            >

              <div
                className="
                  flex
                  items-start
                  justify-between
                  gap-3
                "
              >

                <div className="min-w-0">

                  <p
                    className="
                      font-bold
                      truncate
                    "
                  >
                    {execution.execution_type}
                  </p>

                  <p
                    className="
                      text-xs
                      text-zinc-500
                      mt-1
                      break-all
                    "
                  >
                    {execution.id}
                  </p>

                </div>

                <StatusBadge
                  status={execution.status}
                />

              </div>

              <div
                className="
                  grid
                  grid-cols-2
                  gap-3
                  mt-4
                  text-sm
                "
              >

                <InfoCard
                  title="Retries"
                  value={
                    String(
                      execution.retry_count || 0
                    )
                  }
                />

                <InfoCard
                  title="Locked"
                  value={
                    execution.recovery_locked
                      ? "Yes"
                      : "No"
                  }
                />

              </div>

              <div className="mt-3">

                <InfoCard
                  title="Next Retry"
                  value={
                    execution.next_retry_at

                      ? new Date(
                          execution.next_retry_at
                        ).toLocaleString(
                          "he-IL"
                        )

                      : "-"
                  }
                />

              </div>

            </div>

          )
        )}

        {executions.length === 0 && (

          <p
            className="
              text-zinc-500
              text-sm
            "
          >
            {emptyText}
          </p>
        )}

      </div>

    </div>
  );
}

function BreakerBadge({
  state,
}: {
  state: string;
}) {
  const variantByState: Record<
    string,
    "success" | "warning" | "danger" | "neutral"
  > = {
    CLOSED: "success",
    HALF_OPEN: "warning",
    OPEN: "danger",
  };

  return (
    <Badge variant={variantByState[state] || "neutral"}>
      {state}
    </Badge>
  );
}

function StatusBadge({
  status,
}: {
  status: string;
}) {
  const successStatuses = new Set([
    "COMPLETED",
    "SUCCESS",
    "RECOVERED",
  ]);
  const warningStatuses = new Set([
    "COMPLETED_WITH_ERRORS",
    "WARNING",
    "LOW_CONFIDENCE",
  ]);
  const dangerStatuses = new Set([
    "FAILED",
    "CRITICAL",
    "DEAD_LETTERED",
  ]);
  const infoStatuses = new Set(["RUNNING"]);

  let variant: "success" | "warning" | "danger" | "info" | "neutral" =
    "neutral";

  if (successStatuses.has(status)) {
    variant = "success";
  } else if (warningStatuses.has(status)) {
    variant = "warning";
  } else if (dangerStatuses.has(status)) {
    variant = "danger";
  } else if (infoStatuses.has(status)) {
    variant = "info";
  }

  return <Badge variant={variant}>{status}</Badge>;
}
