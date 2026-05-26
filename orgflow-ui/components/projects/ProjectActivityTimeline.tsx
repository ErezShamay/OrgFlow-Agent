type Activity = {
  id: string;
  activity_type: string;
  title: string;
  description: string | null;
  created_at: string;
};

type Props = {
  activities: Activity[];
};

export default function ProjectActivityTimeline({
  activities,
}: Props) {

  function formatDate(
    value: string
  ) {

    try {

      return new Date(value)
        .toLocaleString("he-IL");

    } catch {

      return value;
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

      <div className="mb-10">

        <h2
          className="
            text-2xl
            font-bold
          "
        >
          ציר פעילות תפעולית
        </h2>

        <p
          className="
            mt-2
            text-zinc-500
          "
        >
          אירועים אחרונים בפרויקט
        </p>

      </div>

      {/* EMPTY STATE */}

      {activities.length === 0 && (

        <div
          className="
            flex
            items-center
            justify-center
            h-40
            rounded-2xl
            border
            border-dashed
            border-zinc-300
            dark:border-zinc-700
            text-zinc-500
          "
        >
          אין פעילות זמינה עדיין
        </div>

      )}

      {/* TIMELINE */}

      {activities.length > 0 && (

        <div className="relative">

          {/* LINE */}

          <div
            className="
              absolute
              right-[5px]
              top-0
              bottom-0
              w-px
              bg-zinc-200
              dark:bg-zinc-800
            "
          />

          <div className="space-y-10">

            {activities.map((activity) => (

              <div
                key={activity.id}
                className="
                  relative
                  flex
                  gap-6
                "
              >

                {/* DOT */}

                <div
                  className="
                    relative
                    z-10
                    mt-2
                    w-3
                    h-3
                    rounded-full
                    bg-blue-500
                    flex-shrink-0
                  "
                />

                {/* CONTENT */}

                <div className="flex-1">

                  <div
                    className="
                      flex
                      justify-between
                      items-start
                      gap-4
                    "
                  >

                    <div>

                      <h3
                        className="
                          font-semibold
                          text-lg
                        "
                      >
                        {activity.title}
                      </h3>

                      {activity.description && (

                        <p
                          className="
                            mt-2
                            text-zinc-600
                            dark:text-zinc-400
                            leading-relaxed
                          "
                        >
                          {activity.description}
                        </p>

                      )}

                    </div>

                    <div
                      className="
                        text-sm
                        text-zinc-500
                        whitespace-nowrap
                      "
                    >
                      {formatDate(
                        activity.created_at
                      )}
                    </div>

                  </div>

                </div>

              </div>

            ))}

          </div>

        </div>

      )}

    </div>

  );
}