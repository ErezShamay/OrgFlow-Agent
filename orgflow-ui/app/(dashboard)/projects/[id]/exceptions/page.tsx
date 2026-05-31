"use client";

import {
  use,
  useCallback,
  useEffect,
  useState,
  startTransition,
} from "react";

import Badge from "@/components/ui/Badge";
import { apiFetch } from "@/lib/api/client";

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

  const loadExceptions = useCallback(async () => {
    try {
      const response =
        await apiFetch(
          `/projects/${resolvedParams.id}/exceptions`
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
  }, [resolvedParams.id]);

  useEffect(() => {
    startTransition(() => {
      void loadExceptions();
    });
  }, [loadExceptions]);

  return (
    <main className="of-dashboard-page">

      <div className="mx-auto max-w-6xl">

        {/* HEADER */}

        <div className="mb-10">

          <h1 className="of-page-title">
            חריגות
          </h1>

          <p className="of-page-desc mt-3">
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

          <div className="of-card of-card-p8">
            אין נקודות סיכון/חריגות פתוחות
          </div>

        )}

        {/* EXCEPTIONS */}

        <div className="grid gap-6">

          {exceptions.map((item) => (

            <div
              key={item.id}
              className="
                of-card
                of-card-p8
                border-red-200
                dark:border-red-900
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

                <Badge variant="danger">
                  חריגה פתוחה
                </Badge>

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