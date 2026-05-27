"use client";

import {
  use,
  useEffect,
  useState,
} from "react";

type Action = {
  id: string;
  action_type: string;
  title: string;
  description: string;
  status: string;
};

type Props = {
  params: Promise<{
    id: string;
  }>;
};

export default function ProjectExceptionsPage({
  params,
}: Props) {

  const resolvedParams =
    use(params);

  const [exceptions, setExceptions] =
    useState<Action[]>([]);

  const [loading, setLoading] =
    useState(true);

  useEffect(() => {
    loadExceptions();
  }, []);

  async function loadExceptions() {

    try {

      const response =
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/projects/${resolvedParams.id}/exceptions`
        );

      const data =
        await response.json();

        if (response.ok && Array.isArray(data)) {
          setExceptions(data);
        } else if (response.ok && data && data.exceptions && Array.isArray(data.exceptions)) {
          setExceptions(data.exceptions);
        } else {
          console.warn('Unexpected exceptions response', data);
          setExceptions([]);
        }

    } catch (error) {

      console.error(error);

    } finally {

      setLoading(false);

    }
  }

  return (
    <main
      className="
        bg-zinc-100
        dark:bg-zinc-950
        text-zinc-900
        dark:text-zinc-100
        min-h-screen
      "
    >

      <div className="max-w-6xl mx-auto px-6 py-10">

        {/* HEADER */}

        <div className="mb-10">

          <h1
            className="
              text-5xl
              font-bold
            "
          >
            חריגות
          </h1>

          <p
            className="
              text-zinc-600
              dark:text-zinc-400
              mt-3
              text-lg
            "
          >
            נקודות סיכון וחריגות בפרויקט
          </p>

        </div>

        {/* LOADING */}

        {loading && (
          <div>
            טוען חריגות...
          </div>
        )}

        {/* EMPTY */}

        {!loading &&
          exceptions.length === 0 && (

          <div
            className="
              bg-white
              dark:bg-zinc-900
              rounded-3xl
              p-8
              border
              border-zinc-200
              dark:border-zinc-800
            "
          >
            אין נקודות סיכון/חריגות פתוחות
          </div>

        )}

        {/* EXCEPTIONS */}

        <div className="grid gap-6">

          {exceptions.map((item) => (

            <div
              key={item.id}
              className="
                bg-white
                dark:bg-zinc-900
                border
                border-red-200
                dark:border-red-900
                rounded-3xl
                p-8
              "
            >

              <div
                className="
                  flex
                  justify-between
                  items-start
                  mb-6
                "
              >

                <div>

                  <h2
                    className="
                      text-2xl
                      font-semibold
                    "
                  >
                    {item.title}
                  </h2>

                  <p
                    className="
                      text-sm
                      text-zinc-500
                      mt-2
                      break-all
                    "
                  >
                    {item.id}
                  </p>

                </div>

                <div
                  className="
                    bg-red-100
                    text-red-700
                    dark:bg-red-900/40
                    dark:text-red-300
                    px-4
                    py-2
                    rounded-full
                    text-sm
                    font-semibold
                  "
                >
                  חריגה פתוחה
                </div>

              </div>

              <div>

                <h3
                  className="
                    font-semibold
                    mb-2
                  "
                >
                  תיאור
                </h3>

                <p
                  className="
                    text-zinc-700
                    dark:text-zinc-300
                    leading-relaxed
                  "
                >
                  {item.description}
                </p>

              </div>

            </div>

          ))}

        </div>

      </div>

    </main>
  );
}