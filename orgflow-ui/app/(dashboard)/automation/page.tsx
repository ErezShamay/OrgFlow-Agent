"use client";

import {
  useEffect,
  useState,
} from "react";

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

export default function AutomationPage() {

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
    loading,
    setLoading
  ] = useState(true);

  useEffect(() => {

    loadData();

  }, []);

  async function loadData() {

    try {

      const [
        statsResponse,
        runsResponse,
      ] = await Promise.all([

        fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/automation/stats`
        ),

        fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/automation/runs`
        ),
      ]);

      const statsData =
        await statsResponse.json();

      const runsData =
        await runsResponse.json();

      setStats(
        statsData
      );

      setRuns(
        runsData
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
        טוען Automation Dashboard...
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

      {/* HEADER */}

      <div className="mb-10">

        <h1
          className="
            text-5xl
            font-black
          "
        >
          Automation Center
        </h1>

        <p
          className="
            mt-4
            text-xl
            text-zinc-600
            dark:text-zinc-400
          "
        >
          ניטור תשתיות אוטומציה ותהליכי AI
        </p>

      </div>

      {/* HEALTH */}

      <div
        className="
          grid
          grid-cols-1
          md:grid-cols-2
          xl:grid-cols-5
          gap-6
        "
      >

        <MetricCard
          title="Automation Health"
          value={
            stats?.health || "-"
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
            (run) => (

              <div
                key={run.id}
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

function StatusBadge({
  status,
}: {
  status: string;
}) {

  const styles = {

    COMPLETED:
      "bg-green-100 text-green-700",

    COMPLETED_WITH_ERRORS:
      "bg-yellow-100 text-yellow-700",

    RUNNING:
      "bg-blue-100 text-blue-700",

    FAILED:
      "bg-red-100 text-red-700",
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