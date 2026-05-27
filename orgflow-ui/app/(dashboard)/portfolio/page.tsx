"use client";

import {
  useEffect,
  useState,
} from "react";

type Prediction = {
  prediction: string;
  risk_score: number;
  message: string;
};

type PortfolioProject = {
  project_id: string;
  project_name: string;

  health: {
    score: number;
    status: string;
  };

  summary: {
    actions_count: number;
    escalations_count: number;
    reviews_count: number;
  };

  prediction: Prediction;
};

type PortfolioResponse = {
  projects: PortfolioProject[];

  critical_projects: number;

  total_projects: number;

  total_actions: number;

  total_escalations: number;

  average_health_score: number;
};

export default function PortfolioPage() {

  const [
    portfolio,
    setPortfolio
  ] = useState<
    PortfolioResponse | null
  >(null);

  const [
    loading,
    setLoading
  ] = useState(true);

  useEffect(() => {

    loadPortfolio();

  }, []);

  async function loadPortfolio() {

    try {

      const response =
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/portfolio/summary`
        );

      if (!response.ok) {

        throw new Error(
          "Failed loading portfolio"
        );
      }

      const data =
        await response.json();

      setPortfolio(data);

    } catch (error) {

      console.error(error);

    } finally {

      setLoading(false);
    }
  }

  if (loading) {

    return (
      <main className="p-10">
        טוען Portfolio...
      </main>
    );
  }

  if (!portfolio) {

    return (
      <main className="p-10">
        Portfolio לא זמין
      </main>
    );
  }

  return (

    <main
      className="
        p-10
        text-zinc-900
        dark:text-zinc-100
      "
    >

      {/* HEADER */}

      <div className="mb-10">

        <p
          className="
            text-zinc-500
            mb-2
          "
        >
          Executive Operations
        </p>

        <h1
          className="
            text-5xl
            font-black
          "
        >
          Portfolio Intelligence
        </h1>

      </div>

      {/* KPI GRID */}

      <div
        className="
          grid
          grid-cols-1
          md:grid-cols-2
          xl:grid-cols-5
          gap-6
        "
      >

        <PortfolioKpiCard
          title="סה״כ פרויקטים"
          value={
            portfolio.total_projects
          }
        />

        <PortfolioKpiCard
          title="פרויקטים קריטיים"
          value={
            portfolio.critical_projects
          }
          danger
        />

        <PortfolioKpiCard
          title="סה״כ פעולות"
          value={
            portfolio.total_actions
          }
        />

        <PortfolioKpiCard
          title="סה״כ הסלמות"
          value={
            portfolio.total_escalations
          }
          danger
        />

        <PortfolioKpiCard
          title="Health ממוצע"
          value={
            portfolio.average_health_score
          }
        />

      </div>

      {/* PROJECTS */}

      <div className="mt-10">

        <h2
          className="
            text-3xl
            font-bold
            mb-6
          "
        >
          דירוג פרויקטים
        </h2>

        <div className="grid gap-6">

          {portfolio.projects.map(
            project => (

              <div
                key={
                  project.project_id
                }
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
                    flex-wrap
                    gap-6
                  "
                >

                  <div className="flex-1">

                    <h3
                      className="
                        text-2xl
                        font-bold
                      "
                    >
                      {
                        project.project_name
                      }
                    </h3>

                    <div
                      className="
                        flex
                        gap-3
                        mt-4
                        flex-wrap
                      "
                    >

                      <Badge>
                        פעולות:
                        {" "}
                        {
                          project.summary
                          .actions_count
                        }
                      </Badge>

                      <Badge>
                        הסלמות:
                        {" "}
                        {
                          project.summary
                          .escalations_count
                        }
                      </Badge>

                      <Badge>
                        ביקורות:
                        {" "}
                        {
                          project.summary
                          .reviews_count
                        }
                      </Badge>

                    </div>

                    {/* PREDICTION */}

                    <div
                      className="
                        mt-6
                        p-5
                        rounded-2xl
                        border
                        border-zinc-200
                        dark:border-zinc-700
                      "
                    >

                      <div
                        className="
                          flex
                          items-center
                          gap-3
                          flex-wrap
                          mb-3
                        "
                      >

                        <PredictionBadge
                          prediction={
                            project
                            .prediction
                            .prediction
                          }
                        />

                        <span
                          className="
                            text-sm
                            text-zinc-500
                          "
                        >
                          Risk Score:
                          {" "}
                          {
                            project
                            .prediction
                            .risk_score
                          }
                        </span>

                      </div>

                      <p
                        className="
                          text-zinc-700
                          dark:text-zinc-300
                          leading-7
                        "
                      >
                        {
                          project
                          .prediction
                          .message
                        }
                      </p>

                    </div>

                  </div>

                  <div
                    className="
                      text-center
                    "
                  >

                    <div
                      className={`
                        w-24
                        h-24
                        rounded-full
                        flex
                        items-center
                        justify-center
                        text-3xl
                        font-black

                        ${
                          project.health
                            .score >= 80

                            ? `
                              bg-green-100
                              text-green-700
                              dark:bg-green-900/30
                              dark:text-green-300
                            `

                            : project.health
                              .score >= 50

                            ? `
                              bg-yellow-100
                              text-yellow-700
                              dark:bg-yellow-900/30
                              dark:text-yellow-300
                            `

                            : `
                              bg-red-100
                              text-red-700
                              dark:bg-red-900/30
                              dark:text-red-300
                            `
                        }
                      `}
                    >
                      {
                        project.health
                        .score
                      }
                    </div>

                    <p
                      className="
                        mt-3
                        text-zinc-500
                      "
                    >
                      Health
                    </p>

                  </div>

                </div>

              </div>

            )
          )}

        </div>

      </div>

    </main>
  );
}

type PortfolioKpiCardProps = {
  title: string;
  value: number;
  danger?: boolean;
};

function PortfolioKpiCard({
  title,
  value,
 danger,
}: PortfolioKpiCardProps) {

  return (

    <div
      className={`
        bg-white
        dark:bg-zinc-900
        border
        rounded-3xl
        p-8

        ${
          danger

            ? `
              border-red-200
              dark:border-red-900
            `

            : `
              border-zinc-200
              dark:border-zinc-800
            `
        }
      `}
    >

      <p
        className={`
          mb-3

          ${
            danger
              ? "text-red-500"
              : "text-zinc-500"
          }
        `}
      >
        {title}
      </p>

      <h2
        className={`
          text-5xl
          font-black

          ${
            danger
              ? "text-red-600"
              : ""
          }
        `}
      >
        {value}
      </h2>

    </div>

  );
}

function Badge({
  children,
}: {
  children: React.ReactNode;
}) {

  return (

    <span
      className="
        text-xs
        px-3
        py-1
        rounded-full
        bg-zinc-100
        dark:bg-zinc-800
      "
    >
      {children}
    </span>

  );
}

function PredictionBadge({
  prediction,
}: {
  prediction: string;
}) {

  if (prediction === "HIGH_RISK") {

    return (

      <span
        className="
          text-xs
          px-3
          py-1
          rounded-full
          bg-red-600
          text-white
        "
      >
        סיכון גבוה
      </span>

    );
  }

  if (prediction === "MEDIUM_RISK") {

    return (

      <span
        className="
          text-xs
          px-3
          py-1
          rounded-full
          bg-yellow-500
          text-white
        "
      >
        סיכון בינוני
      </span>

    );
  }

  return (

    <span
      className="
        text-xs
        px-3
        py-1
        rounded-full
        bg-green-600
        text-white
      "
    >
      סיכון נמוך
    </span>

  );
}