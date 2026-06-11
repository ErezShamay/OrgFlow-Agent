"use client";

// @ts-ignore: allow implicit any for react in this file
import { useEffect, useState } from "react";

type CircuitBreaker = {
  id: string;
  breaker_key: string;
  state: string;
  failure_count?: number;
  cooldown_until?: string | null;
  last_failure_at?: string | null;
};

type CircuitBreakerDashboard = {
  circuit_breakers: CircuitBreaker[];
  breaker_count: number;
  metrics: {
    total_breakers: number;
    open_count: number;
    half_open_count: number;
    closed_count: number;
    total_failures: number;
  };
  analytics: {
    by_state: Record<string, number>;
    by_service: Record<string, number>;
    open_rate: number;
  };
  degradation: {
    mode: string;
    affected_services: string[];
    features_disabled: string[];
  };
  health: {
    score: number;
    status: string;
    service_scores: Array<{
      service: string;
      score: number;
      status: string;
    }>;
  };
  outages: {
    active_outage_count: number;
    outages: Array<{
      breaker_key: string;
      service: string;
      severity: string;
    }>;
  };
  dependencies: {
    total_dependencies: number;
    healthy_count: number;
    unhealthy_count: number;
    dependencies: Array<{
      dependency: string;
      status: string;
      breaker_state: string | null;
    }>;
  };
  ai_failover: {
    primary_provider: string | null;
    selected_provider: string | null;
    failover_active: boolean;
    isolated_providers: string[];
  };
};

declare const process: {
  env: {
    NEXT_PUBLIC_API_URL?: string;
  };
};

export default function CircuitBreakersPage() {
  const [dashboard, setDashboard] = useState<CircuitBreakerDashboard | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [actionKey, setActionKey] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      setLoading(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/automation/circuit-breakers/dashboard`
      );
      if (!response.ok) {
        throw new Error("Failed loading circuit breaker dashboard");
      }
      const data = await response.json();
      setDashboard(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  async function reopenBreaker(breakerKey: string, forceClosed = false) {
    setActionKey(breakerKey);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/automation/circuit-breakers/${encodeURIComponent(breakerKey)}/reopen`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            initiated_by: "dashboard-operator",
            force_closed: forceClosed,
          }),
        }
      );
      if (!response.ok) {
        throw new Error("Reopen failed");
      }
      await loadDashboard();
    } catch (error) {
      console.error(error);
    } finally {
      setActionKey(null);
    }
  }

  const breakers = dashboard?.circuit_breakers || [];

  if (loading && !dashboard) {
    return (
      <main className="p-10">
        טוען Circuit Breaker Dashboard...
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
          Circuit Breaker Dashboard
        </h1>
        <p
          className="
            mt-4
            text-xl
            text-zinc-600
            dark:text-zinc-400
          "
        >
          ניטור תקלות, סף כשלים, שחזור אוטומטי ו-failover לספקי AI
        </p>
      </div>

      <div
        className="
          grid
          grid-cols-1
          md:grid-cols-4
          gap-4
          mb-10
        "
      >
        <StatCard
          label="Breakers"
          value={dashboard?.metrics.total_breakers || 0}
        />
        <StatCard
          label="Open"
          value={dashboard?.metrics.open_count || 0}
          tone="danger"
        />
        <StatCard
          label="Health Score"
          value={dashboard?.health.score || 100}
        />
        <StatCard
          label="Degradation"
          valueText={dashboard?.degradation.mode || "HEALTHY"}
        />
      </div>

      <div
        className="
          grid
          grid-cols-1
          lg:grid-cols-2
          gap-6
          mb-10
        "
      >
        <Panel title="AI Failover">
          <p>Primary: {dashboard?.ai_failover.primary_provider || "-"}</p>
          <p>Selected: {dashboard?.ai_failover.selected_provider || "-"}</p>
          <p>
            Failover active:{" "}
            {dashboard?.ai_failover.failover_active ? "Yes" : "No"}
          </p>
          <p>
            Isolated:{" "}
            {dashboard?.ai_failover.isolated_providers?.join(", ") || "None"}
          </p>
        </Panel>

        <Panel title="Outages">
          <p>Active: {dashboard?.outages.active_outage_count || 0}</p>
          {(dashboard?.outages.outages || []).map((outage) => (
            <p key={outage.breaker_key} className="text-sm text-zinc-500">
              {outage.breaker_key} ({outage.severity})
            </p>
          ))}
        </Panel>
      </div>

      <div
        className="
          bg-white
          dark:bg-zinc-900
          border
          border-zinc-200
          dark:border-zinc-800
          rounded-3xl
          overflow-hidden
        "
      >
        <table className="w-full text-left">
          <thead className="bg-zinc-50 dark:bg-zinc-800">
            <tr>
              <th className="p-4">Breaker</th>
              <th className="p-4">State</th>
              <th className="p-4">Failures</th>
              <th className="p-4">Cooldown</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {breakers.map((breaker) => (
              <tr
                key={breaker.id || breaker.breaker_key}
                className="border-t border-zinc-100 dark:border-zinc-800"
              >
                <td className="p-4 font-mono text-sm">
                  {breaker.breaker_key}
                </td>
                <td className="p-4">{breaker.state}</td>
                <td className="p-4">{breaker.failure_count || 0}</td>
                <td className="p-4 text-sm">
                  {breaker.cooldown_until || "-"}
                </td>
                <td className="p-4">
                  {breaker.state === "OPEN" && (
                    <button
                      className="px-3 py-1 rounded-lg bg-blue-600 text-white text-sm mr-2"
                      disabled={actionKey === breaker.breaker_key}
                      onClick={() => reopenBreaker(breaker.breaker_key)}
                    >
                      Reopen
                    </button>
                  )}
                  {breaker.state !== "CLOSED" && (
                    <button
                      className="px-3 py-1 rounded-lg bg-zinc-700 text-white text-sm"
                      disabled={actionKey === breaker.breaker_key}
                      onClick={() =>
                        reopenBreaker(breaker.breaker_key, true)
                      }
                    >
                      Force Close
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {breakers.length === 0 && (
              <tr>
                <td colSpan={5} className="p-8 text-center text-zinc-500">
                  No circuit breakers recorded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}

function StatCard({
  label,
  value,
  valueText,
  tone,
}: {
  label: string;
  value?: number;
  valueText?: string;
  tone?: "danger";
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
        p-6
      "
    >
      <p className="text-sm text-zinc-500">{label}</p>
      <p
        className={`text-4xl font-black mt-2 ${
          tone === "danger" ? "text-red-600" : ""
        }`}
      >
        {valueText ?? value}
      </p>
    </div>
  );
}

function Panel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
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
        p-6
      "
    >
      <h2 className="text-xl font-bold mb-4">{title}</h2>
      <div className="space-y-2 text-zinc-600 dark:text-zinc-300">
        {children}
      </div>
    </div>
  );
}
