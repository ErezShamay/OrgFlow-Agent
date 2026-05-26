type Insight = {
  type: string;
  title: string;
  description: string;
};

type Props = {
  insights: Insight[];
};

export default function ProjectInsightsPanel({
  insights,
}: Props) {

  function getInsightStyles(
    type: string
  ) {

    switch (type) {

      case "RISK":

        return `
          border-red-200
          dark:border-red-900
          bg-red-50
          dark:bg-red-950/30
        `;

      case "OPERATIONS":

        return `
          border-orange-200
          dark:border-orange-900
          bg-orange-50
          dark:bg-orange-950/30
        `;

      case "POSITIVE":

        return `
          border-green-200
          dark:border-green-900
          bg-green-50
          dark:bg-green-950/30
        `;

      default:

        return `
          border-zinc-200
          dark:border-zinc-800
          bg-white
          dark:bg-zinc-900
        `;
    }
  }

  return (

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

      {/* HEADER */}

      <div className="mb-8">

        <h2
          className="
            text-2xl
            font-bold
          "
        >
          תובנות AI
        </h2>

        <p
          className="
            mt-2
            text-zinc-500
          "
        >
          ניתוח תפעולי מבוסס AI
        </p>

      </div>

      {/* EMPTY */}

      {insights.length === 0 && (

        <div
          className="
            text-zinc-500
          "
        >
          אין תובנות זמינות
        </div>

      )}

      {/* INSIGHTS */}

      <div className="space-y-4">

        {insights.map((insight, index) => (

          <div
            key={index}
            className={`
              border
              rounded-2xl
              p-5
              ${getInsightStyles(
                insight.type
              )}
            `}
          >

            <h3
              className="
                font-bold
                text-lg
              "
            >
              {insight.title}
            </h3>

            <p
              className="
                mt-2
                text-sm
                text-zinc-700
                dark:text-zinc-300
                leading-relaxed
              "
            >
              {insight.description}
            </p>

          </div>

        ))}

      </div>

    </div>

  );
}