"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  useAuth,
} from "@/contexts/AuthContext";
import {
  useCanManageOrganizations,
  useIsPlatformAdmin,
} from "@/hooks/useEffectiveRole";
import { apiFetch } from "@/lib/api/client";

type Organization = {
  id: string;
  organization_name?: string;
  name?: string;
  contact_email?: string;
};

export default function OrgSwitcher() {
  const {
    organizations,
    currentOrgId,
    switchOrganization,
    loading,
  } = useAuth();

  const isPlatformAdminUser = useIsPlatformAdmin();
  const [targetOrgId, setTargetOrgId] = useState<string | null>(null);
  const switching = targetOrgId !== null && targetOrgId !== currentOrgId;
  const hasMultipleOrganizations = organizations.length > 1;
  const shouldShow =
    !loading
    && isPlatformAdminUser
    && organizations.length > 0;

  if (!shouldShow) {
    return null;
  }

  const canSwitch = hasMultipleOrganizations;

  const labelFor = (organization: Organization) =>
    organization.organization_name
    || organization.name
    || organization.contact_email
    || organization.id;

  return (
    <label className="inline-flex items-center gap-2">
      <span className="text-xs font-medium text-zinc-500">
        לקוח
      </span>
      <select
        value={currentOrgId || ""}
        disabled={switching || !canSwitch}
        title={
          canSwitch
            ? undefined
            : "יש לקוח אחד במערכת - הוסף לקוח נוסף כדי לעבור ביניהם"
        }
        onChange={(event) => {
          const nextOrgId = event.target.value;

          if (!canSwitch || !nextOrgId || nextOrgId === currentOrgId) {
            return;
          }

          setTargetOrgId(nextOrgId);
          void switchOrganization(nextOrgId).finally(() => {
            setTargetOrgId(null);
          });
        }}
        className="
          of-input
          of-focus-ring
          min-w-[10rem]
          px-3
          py-2
          text-sm
        "
      >
        {organizations.map((organization) => (
          <option key={organization.id} value={organization.id}>
            {labelFor(organization)}
          </option>
        ))}
      </select>
    </label>
  );
}

export function TenantMigrationBanner() {
  const canManageOrganizations = useCanManageOrganizations();
  const [status, setStatus] = useState<{
    ready: boolean;
    migration_sql_path?: string;
  } | null>(null);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    void apiFetch("/admin/tenant-migration/status")
      .then(async (response) => {
        if (!response.ok) {
          return;
        }

        setStatus(await response.json());
      })
      .catch(() => {
        // Ignore when user is not admin.
      });
  }, []);

  if (!canManageOrganizations || !status || status.ready) {
    return null;
  }

  async function runBackfill() {
    try {
      setRunning(true);
      setMessage("");

      const response = await apiFetch(
        "/admin/tenant-migration/backfill",
        { method: "POST" }
      );
      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.error?.message
          || data?.detail
          || "Backfill failed"
        );
      }

      setMessage(
        data.status === "completed"
          ? data.message
            || "השיוך ללקוח היחיד הושלם. רענן את הדף."
          : data.message
            || `יש להריץ קודם את המיגרציה: ${data.migration_sql_path}`
      );
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Backfill failed"
      );
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="mb-6 rounded-2xl border border-amber-300/80 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
      <p className="font-semibold">
        נדרשת הגדרת הפרדת לקוחות
      </p>
      <p className="mt-2">
        כרגע יש במערכת לקוח אחד - כל המשתמשים והפרויקטים הקיימים
        ישויכו אליו. הרץ את קובץ המיגרציה{" "}
        <code className="rounded bg-white/70 px-1 dark:bg-black/30">
          {status.migration_sql_path}
        </code>{" "}
        ב-Supabase SQL Editor, ואז לחץ על השלמת שיוך.
      </p>
      <button
        type="button"
        onClick={() => void runBackfill()}
        disabled={running}
        className="mt-3 rounded-xl bg-amber-600 px-4 py-2 font-medium text-white hover:bg-amber-700 disabled:opacity-60"
      >
        {running ? "מריץ..." : "שיוך ללקוח הקיים"}
      </button>
      {message ? (
        <p className="mt-3">{message}</p>
      ) : null}
    </div>
  );
}
