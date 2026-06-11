"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import PlatformAdminGuard from "@/components/admin/PlatformAdminGuard";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { ADMIN_USERS_ROUTE } from "@/lib/navigation";
import { apiFetch } from "@/lib/api/client";

type PromptUsageSummary = {
  prompt_name: string;
  total_calls: number;
  total_tokens: number;
  estimated_cost_usd: number;
};

type OrganizationAIUsageSummary = {
  organization_id: string;
  organization_name: string;
  contact_email?: string | null;
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  cache_hits: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  last_activity_at?: string | null;
  usage_by_prompt: PromptUsageSummary[];
};

type PlatformAIUsageTotals = {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  cache_hits: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  active_organizations: number;
};

type PlatformAIUsageDashboard = {
  period_days: number;
  generated_at: string;
  pricing_disclaimer: string;
  totals: PlatformAIUsageTotals;
  organizations: OrganizationAIUsageSummary[];
};

function formatNumber(
  value: number
): string {
  return new Intl.NumberFormat("he-IL").format(value);
}

function formatUsd(
  value: number
): string {
  if (value === 0) {
    return "$0.00";
  }

  if (value < 0.01) {
    return `$${value.toFixed(4)}`;
  }

  return `$${value.toFixed(2)}`;
}

function formatDate(
  value?: string | null
): string {
  if (!value) {
    return "אין פעילות";
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return "אין פעילות";
  }

  return new Intl.DateTimeFormat("he-IL", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

export default function PlatformAdminDashboardPage() {
  return (
    <PlatformAdminGuard>
      <PlatformAdminDashboardContent />
    </PlatformAdminGuard>
  );
}

function PlatformAdminDashboardContent() {
  const [dashboard, setDashboard] = useState<
    PlatformAIUsageDashboard | null
  >(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedOrgId, setExpandedOrgId] = useState<string | null>(
    null
  );
  const [periodDays, setPeriodDays] = useState(90);

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const response = await apiFetch(
        `/admin/ai-usage?period_days=${periodDays}`
      );
      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.error?.message
          || data?.detail
          || "טעינת דשבורד נכשלה"
        );
      }

      setDashboard(data);
    } catch (loadError) {
      setDashboard(null);
      setError(
        loadError instanceof Error
          ? loadError.message
          : "טעינת דשבורד נכשלה"
      );
    } finally {
      setLoading(false);
    }
  }, [periodDays]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const summaryCards = useMemo(() => {
    if (!dashboard) {
      return [];
    }

    const { totals } = dashboard;

    return [
      {
        label: "לקוחות פעילים",
        value: formatNumber(totals.active_organizations),
      },
      {
        label: "קריאות AI",
        value: formatNumber(totals.total_calls),
      },
      {
        label: "טוקנים",
        value: formatNumber(totals.total_tokens),
      },
      {
        label: "עלות משוערת",
        value: formatUsd(totals.estimated_cost_usd),
      },
    ];
  }, [dashboard]);

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-4 md:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-2">
          <p className="text-sm font-medium text-zinc-500">
            ניהול פלטפורמה
          </p>
          <h1 className="text-3xl font-semibold tracking-tight">
            דשבורד שימוש בינה מלאכותית לפי לקוח
          </h1>
          <p className="max-w-3xl text-sm leading-6 text-zinc-600 dark:text-zinc-300">
            {dashboard?.pricing_disclaimer
              || "שימוש בבינה מלאכותית כלול במחיר הבסיסי. בהתאם לנפח השימוש בפועל, ייתכן עדכון תמחור בעתיד."}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <label className="inline-flex items-center gap-2 text-sm text-zinc-600">
            <span>תקופה</span>
            <select
              value={periodDays}
              onChange={(event) => {
                setPeriodDays(Number(event.target.value));
              }}
              className="of-input of-focus-ring px-3 py-2"
            >
              <option value={30}>30 ימים</option>
              <option value={90}>90 ימים</option>
              <option value={180}>180 ימים</option>
            </select>
          </label>

          <Button
            type="button"
            variant="secondary"
            onClick={() => void loadDashboard()}
            disabled={loading}
          >
            רענון
          </Button>

          <Link
            href={ADMIN_USERS_ROUTE.href}
            className="of-btn of-btn-primary px-4 py-2 text-sm"
          >
            ניהול משתמשים
          </Link>
        </div>
      </div>

      {error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          {error}
        </div>
      ) : null}

      {loading && !dashboard ? (
        <p className="text-sm text-zinc-500">טוען נתוני שימוש...</p>
      ) : null}

      {dashboard ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {summaryCards.map((card) => (
              <div
                key={card.label}
                className="rounded-2xl border border-zinc-200/80 bg-white/80 p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-950/40"
              >
                <p className="text-sm text-zinc-500">{card.label}</p>
                <p className="mt-2 text-2xl font-semibold">
                  {card.value}
                </p>
              </div>
            ))}
          </div>

          <div className="overflow-hidden rounded-2xl border border-zinc-200/80 bg-white/80 shadow-sm dark:border-zinc-800 dark:bg-zinc-950/40">
            <div className="border-b border-zinc-200/80 px-5 py-4 dark:border-zinc-800">
              <h2 className="text-lg font-semibold">
                פירוט לפי לקוח
              </h2>
              <p className="mt-1 text-sm text-zinc-500">
                עודכן לאחרונה: {formatDate(dashboard.generated_at)}
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-zinc-50 text-right text-zinc-500 dark:bg-zinc-900/60">
                  <tr>
                    <th className="px-5 py-3 font-medium">לקוח</th>
                    <th className="px-5 py-3 font-medium">קריאות</th>
                    <th className="px-5 py-3 font-medium">טוקנים</th>
                    <th className="px-5 py-3 font-medium">מטמון</th>
                    <th className="px-5 py-3 font-medium">עלות משוערת</th>
                    <th className="px-5 py-3 font-medium">פעילות אחרונה</th>
                    <th className="px-5 py-3 font-medium">פירוט</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboard.organizations.map((organization) => {
                    const isExpanded =
                      expandedOrgId === organization.organization_id;
                    const isActive = organization.total_calls > 0;

                    return (
                      <tr
                        key={organization.organization_id}
                        className="border-t border-zinc-200/80 align-top dark:border-zinc-800"
                      >
                        <td className="px-5 py-4">
                          <div className="space-y-1">
                            <p className="font-medium">
                              {organization.organization_name}
                            </p>
                            {organization.contact_email ? (
                              <p className="text-xs text-zinc-500">
                                {organization.contact_email}
                              </p>
                            ) : null}
                            {!isActive ? (
                              <Badge variant="neutral">
                                ללא שימוש
                              </Badge>
                            ) : null}
                          </div>

                          {isExpanded ? (
                            <div className="mt-4 space-y-2 rounded-xl bg-zinc-50 p-3 text-xs dark:bg-zinc-900/60">
                              <p className="font-medium text-zinc-700 dark:text-zinc-200">
                                שימוש לפי סוג פעולה
                              </p>
                              {organization.usage_by_prompt.length > 0 ? (
                                organization.usage_by_prompt.map((item) => (
                                  <div
                                    key={item.prompt_name}
                                    className="flex flex-wrap items-center justify-between gap-2"
                                  >
                                    <span>{item.prompt_name}</span>
                                    <span className="text-zinc-500">
                                      {formatNumber(item.total_calls)} קריאות ·{" "}
                                      {formatNumber(item.total_tokens)} טוקנים ·{" "}
                                      {formatUsd(item.estimated_cost_usd)}
                                    </span>
                                  </div>
                                ))
                              ) : (
                                <p className="text-zinc-500">
                                  אין פירוט זמין
                                </p>
                              )}
                            </div>
                          ) : null}
                        </td>
                        <td className="px-5 py-4">
                          {formatNumber(organization.total_calls)}
                        </td>
                        <td className="px-5 py-4">
                          {formatNumber(organization.total_tokens)}
                        </td>
                        <td className="px-5 py-4">
                          {formatNumber(organization.cache_hits)}
                        </td>
                        <td className="px-5 py-4">
                          {formatUsd(organization.estimated_cost_usd)}
                        </td>
                        <td className="px-5 py-4">
                          {formatDate(organization.last_activity_at)}
                        </td>
                        <td className="px-5 py-4">
                          <button
                            type="button"
                            className="text-sm font-medium text-blue-600 hover:underline dark:text-blue-400"
                            onClick={() => {
                              setExpandedOrgId(
                                isExpanded
                                  ? null
                                  : organization.organization_id
                              );
                            }}
                          >
                            {isExpanded ? "סגור" : "הצג"}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
