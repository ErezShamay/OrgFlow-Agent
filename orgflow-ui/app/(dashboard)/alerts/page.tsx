"use client";

import { useAlerts } from "@/hooks/useAlerts";

export default function AlertsPage() {

  const {
    alerts,
    loading,
  } = useAlerts();

  if (loading) {

    return (
      <main className="of-dashboard-page">
        טוען התראות...
      </main>
    );
  }

  return (

    <main className="of-dashboard-page">

      <div className="mb-10">

        <p
          className="
            text-zinc-500
            mb-2
          "
        >
          AI Operational Monitoring
        </p>

        <h1 className="of-page-title">
          מרכז התראות
        </h1>

      </div>

      {alerts.length === 0 && (

        <div className="of-card of-card-p10 of-card-xl">
          אין התראות פעילות
        </div>

      )}

      <div className="grid gap-6">

        {alerts.map((alert, index) => (

          <div
            key={index}
            className={`
              border
              rounded-3xl
              p-8

              ${
                alert.severity
                === "CRITICAL"

                  ? `
                    bg-red-50
                    border-red-200
                    dark:bg-red-950/20
                    dark:border-red-900
                  `

                  : `
                    bg-yellow-50
                    border-yellow-200
                    dark:bg-yellow-950/20
                    dark:border-yellow-900
                  `
              }
            `}
          >

            <div
              className="
                flex
                items-center
                justify-between
                flex-wrap
                gap-4
                mb-5
              "
            >

              <div>

                <h2
                  className="
                    text-2xl
                    font-bold
                  "
                >
                  {alert.title}
                </h2>

                <p
                  className="
                    text-zinc-500
                    mt-2
                  "
                >
                  {alert.project_name}
                </p>

              </div>

              <span
                className={`
                  text-xs
                  px-3
                  py-1
                  rounded-full
                  text-white

                  ${
                    alert.severity
                    === "CRITICAL"

                      ? "bg-red-600"

                      : "bg-yellow-600"
                  }
                `}
              >
                {alert.severity}
              </span>

            </div>

            <p
              className="
                leading-8
                text-lg
              "
            >
              {alert.message}
            </p>

          </div>

        ))}

      </div>

    </main>

  );
}
