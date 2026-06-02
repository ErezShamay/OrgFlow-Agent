"use client";

import {
  FormEvent,
  useEffect,
  useMemo,
  useState,
} from "react";

import { toast } from "sonner";

import AdminGuard from "@/components/admin/AdminGuard";
import { TenantMigrationBanner } from "@/components/admin/OrgSwitcher";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { useAuth } from "@/contexts/AuthContext";
import {
  useCanManageOrganizations,
} from "@/hooks/useEffectiveRole";
import { inviteableRoles, organizationHasClientAdmin } from "@/lib/auth/permissions";
import { getRoleLabel } from "@/lib/auth/roleLabels";
import { apiFetch } from "@/lib/api/client";

type ManagedUser = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  account_status?: "pending" | "active";
  created_at?: string | null;
};

type CustomerOrganization = {
  id: string;
  organization_name?: string;
  name?: string;
  contact_email?: string;
};

type FieldReportModuleRow = {
  organization_id: string;
  organization_name: string;
  contact_email?: string;
  is_enabled: boolean;
  unsent_drafts_count?: number;
};

type FieldReportModulesResponse = {
  organizations: FieldReportModuleRow[];
  storage_available?: boolean;
};

type OrganizationReportProfile = {
  organization_id: string;
  organization_name: string;
  contact_email?: string | null;
  report_phone?: string | null;
  report_address_line?: string | null;
  report_city?: string | null;
  report_tagline?: string | null;
  logo_storage_path?: string | null;
  logo_url?: string | null;
};

export default function AdminUsersPage() {
  return (
    <AdminGuard>
      <AdminUsersContent />
    </AdminGuard>
  );
}

function AdminUsersContent() {
  const { profile, currentOrgId, sessionRole } = useAuth();
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const canManageOrganizations = useCanManageOrganizations();
  const effectiveRole = profile?.role || sessionRole;
  const hasClientAdmin = organizationHasClientAdmin(users);
  const [role, setRole] = useState<string>("VIEWER");
  const roleOptions = useMemo(
    () => [
      ...inviteableRoles(effectiveRole, {
        hasClientAdmin,
      }),
    ] as Array<"ADMIN" | "SUPERVISOR" | "VIEWER">,
    [effectiveRole, hasClientAdmin],
  );
  const selectedRole = roleOptions.includes(
    role as (typeof roleOptions)[number]
  )
    ? role
    : (roleOptions[0] ?? "VIEWER");

  const [customerOrganizations, setCustomerOrganizations] =
    useState<CustomerOrganization[]>([]);
  const [fieldReportModules, setFieldReportModules] = useState<
    FieldReportModuleRow[]
  >([]);
  const [fieldReportStorageAvailable, setFieldReportStorageAvailable] =
    useState(true);
  const [togglingModuleOrgId, setTogglingModuleOrgId] = useState<
    string | null
  >(null);
  const [editingProfileOrgId, setEditingProfileOrgId] = useState<
    string | null
  >(null);
  const [loadingProfileOrgId, setLoadingProfileOrgId] = useState<
    string | null
  >(null);
  const [savingProfileOrgId, setSavingProfileOrgId] = useState<
    string | null
  >(null);
  const [profileForm, setProfileForm] = useState({
    report_phone: "",
    report_address_line: "",
    report_city: "",
    report_tagline: "",
    logo_storage_path: "",
  });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [creatingOrganization, setCreatingOrganization] = useState(false);
  const [deletingUserId, setDeletingUserId] = useState<string | null>(null);
  const [resendingUserId, setResendingUserId] = useState<string | null>(null);
  const [resettingUserId, setResettingUserId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [organizationName, setOrganizationName] = useState("");
  const [organizationEmail, setOrganizationEmail] = useState("");

  useEffect(() => {
    void loadUsers();
    void loadOrganizations();
    if (canManageOrganizations) {
      void loadFieldReportModules();
    }
  }, [currentOrgId, canManageOrganizations]);

  async function loadOrganizations() {
    try {
      const response = await apiFetch("/admin/organizations");

      if (!response.ok) {
        return;
      }

      const data = await response.json();
      setCustomerOrganizations(data.organizations || []);
    } catch {
      setCustomerOrganizations([]);
    }
  }

  async function loadFieldReportModules() {
    try {
      const response = await apiFetch("/admin/field-reports/modules");

      if (!response.ok) {
        return;
      }

      const data = (await response.json()) as FieldReportModulesResponse;
      setFieldReportModules(data.organizations || []);
      setFieldReportStorageAvailable(
        data.storage_available !== false
      );
    } catch {
      setFieldReportModules([]);
    }
  }

  async function handleToggleFieldReportModule(
    organizationId: string,
    nextEnabled: boolean
  ) {
    try {
      setTogglingModuleOrgId(organizationId);
      setError("");

      const response = await apiFetch(
        `/admin/field-reports/modules/${organizationId}`,
        {
          method: "PATCH",
          body: JSON.stringify({ is_enabled: nextEnabled }),
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data?.error?.message
          || data?.detail
          || "עדכון מודול הפקת דוחות נכשל"
        );
      }

      toast.success(
        nextEnabled
          ? "מודול הפקת דוחות הופעל"
          : "מודול הפקת דוחות כובה"
      );
      await loadFieldReportModules();
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "עדכון מודול הפקת דוחות נכשל";
      setError(message);
      toast.error(message);
    } finally {
      setTogglingModuleOrgId(null);
    }
  }

  function resetProfileForm(profile?: OrganizationReportProfile) {
    setProfileForm({
      report_phone: profile?.report_phone || "",
      report_address_line: profile?.report_address_line || "",
      report_city: profile?.report_city || "",
      report_tagline: profile?.report_tagline || "",
      logo_storage_path: profile?.logo_storage_path || "",
    });
  }

  async function handleEditFieldReportProfile(
    organizationId: string
  ) {
    try {
      setLoadingProfileOrgId(organizationId);
      setError("");

      const response = await apiFetch(
        `/admin/field-reports/organizations/${organizationId}/profile`
      );
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data?.error?.message
            || data?.detail
            || "טעינת פרופיל ארגון לדוחות נכשלה"
        );
      }

      resetProfileForm(data as OrganizationReportProfile);
      setEditingProfileOrgId(organizationId);
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "טעינת פרופיל ארגון לדוחות נכשלה";
      setError(message);
      toast.error(message);
    } finally {
      setLoadingProfileOrgId(null);
    }
  }

  async function handleSaveFieldReportProfile(
    organizationId: string
  ) {
    try {
      setSavingProfileOrgId(organizationId);
      setError("");

      const response = await apiFetch(
        `/admin/field-reports/organizations/${organizationId}/profile`,
        {
          method: "PATCH",
          body: JSON.stringify({
            report_phone: profileForm.report_phone || null,
            report_address_line: profileForm.report_address_line || null,
            report_city: profileForm.report_city || null,
            report_tagline: profileForm.report_tagline || null,
            logo_storage_path: profileForm.logo_storage_path || null,
          }),
        }
      );
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data?.error?.message
            || data?.detail
            || "שמירת פרופיל הארגון נכשלה"
        );
      }

      resetProfileForm(data as OrganizationReportProfile);
      toast.success("פרופיל ארגון לדוחות נשמר");
      setEditingProfileOrgId(null);
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "שמירת פרופיל הארגון נכשלה";
      setError(message);
      toast.error(message);
    } finally {
      setSavingProfileOrgId(null);
    }
  }

  async function loadUsers() {
    try {
      setLoading(true);
      setError("");

      const response = await apiFetch("/admin/users");

      if (!response.ok) {
        throw new Error("טעינת המשתמשים נכשלה");
      }

      const data = await response.json();
      setUsers(data.users || []);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "טעינת המשתמשים נכשלה"
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateOrganization(e: FormEvent) {
    e.preventDefault();

    try {
      setCreatingOrganization(true);
      setError("");

      const response = await apiFetch("/admin/organizations", {
        method: "POST",
        body: JSON.stringify({
          organization_name: organizationName,
          contact_email: organizationEmail,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data?.error?.message
          || data?.detail
          || "יצירת הלקוח נכשלה"
        );
      }

      toast.success("הלקוח נוצר בהצלחה");
      setOrganizationName("");
      setOrganizationEmail("");
      await loadOrganizations();
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "יצירת הלקוח נכשלה";
      setError(message);
      toast.error(message);
    } finally {
      setCreatingOrganization(false);
    }
  }

  async function handleInvite(e: FormEvent) {
    e.preventDefault();

    try {
      setSubmitting(true);
      setError("");

      const response = await apiFetch("/admin/users", {
        method: "POST",
        body: JSON.stringify({
          email,
          full_name: fullName,
          role: selectedRole,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data?.error?.message
          || data?.detail
          || "שליחת ההזמנה נכשלה"
        );
      }

      if (data.email_status === "SENT") {
        toast.success("ההזמנה נשלחה בהצלחה");
      } else {
        toast.warning(
          "המשתמש נוצר, אך שליחת המייל נכשלה. בדקו את הגדרות המייל."
        );
      }

      setEmail("");
      setFullName("");
      setRole("VIEWER");
      await loadUsers();
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "שליחת ההזמנה נכשלה";
      setError(message);
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResendInvite(user: ManagedUser) {
    if (user.account_status === "active") {
      toast.error("המשתמש כבר הפעיל את החשבון. השתמשו באיפוס סיסמה.");
      return;
    }

    try {
      setResendingUserId(user.id);
      setError("");

      const response = await apiFetch(
        `/admin/users/${user.id}/resend-invite`,
        { method: "POST" }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data?.error?.message
          || data?.detail
          || "שליחת ההזמנה מחדש נכשלה"
        );
      }

      if (data.email_status === "SENT") {
        toast.success("ההזמנה נשלחה מחדש");
      } else {
        toast.warning("יצירת הקישור הצליחה, אך שליחת המייל נכשלה");
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "שליחת ההזמנה מחדש נכשלה";
      setError(message);
      toast.error(message);
    } finally {
      setResendingUserId(null);
    }
  }

  async function handlePasswordReset(user: ManagedUser) {
    const confirmed = window.confirm(
      `לשלוח למשתמש ${user.full_name || user.email} מייל לאיפוס סיסמה?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setResettingUserId(user.id);
      setError("");

      const response = await apiFetch(
        `/admin/users/${user.id}/password-reset`,
        { method: "POST" }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data?.error?.message
          || data?.detail
          || "שליחת איפוס הסיסמה נכשלה"
        );
      }

      if (data.email_status === "SENT") {
        toast.success("מייל איפוס סיסמה נשלח");
      } else {
        toast.warning("יצירת הקישור הצליחה, אך שליחת המייל נכשלה");
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "שליחת איפוס הסיסמה נכשלה";
      setError(message);
      toast.error(message);
    } finally {
      setResettingUserId(null);
    }
  }

  async function handleDelete(user: ManagedUser) {
    if (user.id === profile?.id) {
      toast.error("לא ניתן למחוק את המשתמש שלך");
      return;
    }

    const confirmed = window.confirm(
      `למחוק את ${user.full_name || user.email}?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingUserId(user.id);
      setError("");

      const response = await apiFetch(
        `/admin/users/${user.id}`,
        { method: "DELETE" }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data?.error?.message
          || data?.detail
          || "מחיקת המשתמש נכשלה"
        );
      }

      toast.success("המשתמש נמחק");
      setUsers((current) =>
        current.filter((item) => item.id !== user.id)
      );
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "מחיקת המשתמש נכשלה";
      setError(message);
      toast.error(message);
    } finally {
      setDeletingUserId(null);
    }
  }

  return (
    <div className="of-dashboard-page of-container mx-auto max-w-5xl space-y-10">
      <header>
        <h1 className="of-page-title text-2xl md:text-3xl">
          ניהול משתמשים
        </h1>
        <p className="of-page-desc max-w-2xl text-sm">
          {canManageOrganizations
            ? "אתה מנהל גלובלי — גישה לכל הלקוחות, יצירת לקוחות חדשים, וניהול משתמשים בכל חברה."
            : "אתה מנהל לקוח — ניהול משתמשים ופעולות רק עבור הלקוח הפעיל."}
        </p>
      </header>

      {canManageOrganizations ? <TenantMigrationBanner /> : null}

      {canManageOrganizations ? (
      <section className="of-card of-card-p6">
        <h2 className="mb-4 text-xl font-semibold">
          לקוחות במערכת
        </h2>

        <form
          onSubmit={handleCreateOrganization}
          className="mb-6 grid gap-4 md:grid-cols-2"
        >
          <div>
            <label className="mb-2 block text-sm font-medium">
              שם הלקוח
            </label>
            <input
              type="text"
              value={organizationName}
              onChange={(e) => setOrganizationName(e.target.value)}
              required
              className="of-input of-focus-ring w-full text-sm"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium">
              אימייל ליצירת קשר
            </label>
            <input
              type="email"
              value={organizationEmail}
              onChange={(e) => setOrganizationEmail(e.target.value)}
              required
              className="of-input of-focus-ring w-full text-sm"
            />
          </div>

          <div className="md:col-span-2">
            <Button
              type="submit"
              variant="secondary"
              disabled={creatingOrganization}
            >
              {creatingOrganization ? "יוצר לקוח..." : "הוספת לקוח חדש"}
            </Button>
          </div>
        </form>

        {customerOrganizations.length > 0 ? (
          <ul className="space-y-2 text-sm">
            {customerOrganizations.map((organization) => (
              <li
                key={organization.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-zinc-200/80 px-4 py-3 dark:border-zinc-800"
              >
                <span className="font-medium">
                  {organization.organization_name
                    || organization.name
                    || "לקוח"}
                </span>
                <span className="text-zinc-500">
                  {organization.contact_email || organization.id}
                </span>
                {organization.id === currentOrgId ? (
                  <Badge>לקוח פעיל</Badge>
                ) : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-zinc-500">
            עדיין לא הוגדרו לקוחות. צור לקוח ראשון כדי להתחיל.
          </p>
        )}

        <div className="mt-10 border-t border-zinc-200/80 pt-8 dark:border-zinc-800">
          <h3 className="mb-2 text-lg font-semibold">
            מודול הפקת דוחות (ספק)
          </h3>
          <p className="mb-4 text-sm text-zinc-500">
            הפעלה וכיבוי לפי ארגון. ארגון ללא מודול לא יכול לגשת לאזור
            «הפקת דוחות».
          </p>

          {!fieldReportStorageAvailable ? (
            <p className="mb-4 text-sm text-amber-700 dark:text-amber-400">
              טבלאות המודול אינן קיימות במסד — יש להריץ את המיגרציות
              2026060101_organization_field_report_module.sql ו-
              2026060102_field_visit_reports.sql
            </p>
          ) : null}

          {fieldReportModules.length > 0 ? (
            <ul className="space-y-2 text-sm">
              {fieldReportModules.map((row) => (
                <li
                  key={row.organization_id}
                  className="rounded-xl border border-zinc-200/80 px-4 py-3 dark:border-zinc-800"
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <span className="font-medium">
                        {row.organization_name}
                      </span>
                      <span className="mx-2 text-zinc-400">·</span>
                      <span className="text-zinc-500">
                        {row.contact_email || row.organization_id}
                      </span>
                      {(row.unsent_drafts_count || 0) > 0 ? (
                        <p className="mt-1 text-xs text-amber-700 dark:text-amber-300">
                          {row.unsent_drafts_count} טיוטות שלא נשלחו לליבה נשמרו
                          לביקורת ספק.
                        </p>
                      ) : null}
                    </div>
                    <div className="flex items-center gap-2">
                      {row.is_enabled ? (
                        <Badge variant="success">מופעל</Badge>
                      ) : (
                        <Badge variant="neutral">כבוי</Badge>
                      )}
                      <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        disabled={
                          !fieldReportStorageAvailable
                          || togglingModuleOrgId === row.organization_id
                        }
                        onClick={() =>
                          void handleToggleFieldReportModule(
                            row.organization_id,
                            !row.is_enabled
                          )
                        }
                      >
                        {togglingModuleOrgId === row.organization_id
                          ? "מעדכן..."
                          : row.is_enabled
                            ? "כיבוי"
                            : "הפעלה"}
                      </Button>
                      <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        disabled={loadingProfileOrgId === row.organization_id}
                        onClick={() =>
                          void handleEditFieldReportProfile(
                            row.organization_id
                          )
                        }
                      >
                        {loadingProfileOrgId === row.organization_id
                          ? "טוען..."
                          : "פרופיל דוח"}
                      </Button>
                    </div>
                  </div>

                  {editingProfileOrgId === row.organization_id ? (
                    <div className="mt-4 grid gap-3 border-t border-zinc-200/80 pt-4 dark:border-zinc-800 md:grid-cols-2">
                      <div>
                        <label className="mb-2 block text-xs font-medium text-zinc-500">
                          טלפון בדוח
                        </label>
                        <input
                          type="text"
                          value={profileForm.report_phone}
                          onChange={(e) =>
                            setProfileForm((current) => ({
                              ...current,
                              report_phone: e.target.value,
                            }))
                          }
                          className="of-input of-focus-ring w-full text-sm"
                        />
                      </div>
                      <div>
                        <label className="mb-2 block text-xs font-medium text-zinc-500">
                          עיר
                        </label>
                        <input
                          type="text"
                          value={profileForm.report_city}
                          onChange={(e) =>
                            setProfileForm((current) => ({
                              ...current,
                              report_city: e.target.value,
                            }))
                          }
                          className="of-input of-focus-ring w-full text-sm"
                        />
                      </div>
                      <div className="md:col-span-2">
                        <label className="mb-2 block text-xs font-medium text-zinc-500">
                          כתובת לדוח
                        </label>
                        <input
                          type="text"
                          value={profileForm.report_address_line}
                          onChange={(e) =>
                            setProfileForm((current) => ({
                              ...current,
                              report_address_line: e.target.value,
                            }))
                          }
                          className="of-input of-focus-ring w-full text-sm"
                        />
                      </div>
                      <div className="md:col-span-2">
                        <label className="mb-2 block text-xs font-medium text-zinc-500">
                          סלוגן/כותרת משנה
                        </label>
                        <input
                          type="text"
                          value={profileForm.report_tagline}
                          onChange={(e) =>
                            setProfileForm((current) => ({
                              ...current,
                              report_tagline: e.target.value,
                            }))
                          }
                          className="of-input of-focus-ring w-full text-sm"
                        />
                      </div>
                      <div className="md:col-span-2">
                        <label className="mb-2 block text-xs font-medium text-zinc-500">
                          לוגו (URL או נתיב storage)
                        </label>
                        <input
                          type="text"
                          value={profileForm.logo_storage_path}
                          onChange={(e) =>
                            setProfileForm((current) => ({
                              ...current,
                              logo_storage_path: e.target.value,
                            }))
                          }
                          className="of-input of-focus-ring w-full text-sm"
                        />
                      </div>
                      <div className="md:col-span-2 flex flex-wrap gap-2">
                        <Button
                          type="button"
                          variant="accent"
                          size="sm"
                          disabled={savingProfileOrgId === row.organization_id}
                          onClick={() =>
                            void handleSaveFieldReportProfile(
                              row.organization_id
                            )
                          }
                        >
                          {savingProfileOrgId === row.organization_id
                            ? "שומר..."
                            : "שמירה"}
                        </Button>
                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          disabled={savingProfileOrgId === row.organization_id}
                          onClick={() => {
                            setEditingProfileOrgId(null);
                            resetProfileForm();
                          }}
                        >
                          ביטול
                        </Button>
                      </div>
                    </div>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-zinc-500">
              אין ארגונים להצגה.
            </p>
          )}
        </div>
      </section>
      ) : null}

      <section className="of-card of-card-p6">
        <h2 className="mb-4 text-xl font-semibold">
          {canManageOrganizations
            ? "הזמנת משתמש ללקוח הפעיל"
            : "הזמנת משתמש לחברה"}
        </h2>
        <p className="mb-4 text-sm text-zinc-500">
          {canManageOrganizations
            ? "משתמשים חדשים ישויכו ללקוח שנבחר ב-switcher למעלה."
            : "משתמשים חדשים ישויכו לחברה שלך בלבד. מנהל לקוח יכול לנהל רק את הארגון שלו."}
          {" "}
          לכל לקוח מותר מנהל לקוח אחד בלבד.
          {hasClientAdmin && canManageOrganizations
            ? " ללקוח הפעיל כבר יש מנהל לקוח — ניתן להזמין מפקח או משתמש כללי."
            : ""}
        </p>

        <form
          onSubmit={handleInvite}
          className="grid gap-4 md:grid-cols-2"
        >
          <div>
            <label className="mb-2 block text-sm font-medium">
              שם מלא
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              className="of-input of-focus-ring w-full text-sm"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium">
              אימייל
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="of-input of-focus-ring w-full text-sm"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium">
              תפקיד
            </label>
            <select
              value={selectedRole}
              onChange={(e) => setRole(e.target.value)}
              className="of-input of-focus-ring w-full text-sm"
            >
              {roleOptions.map((option) => (
                <option key={option} value={option}>
                  {getRoleLabel(option)}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <Button
              type="submit"
              variant="accent"
              disabled={submitting}
              className="w-full md:w-auto"
            >
              {submitting ? "שולח הזמנה..." : "שליחת הזמנה"}
            </Button>
          </div>
        </form>
      </section>

      <section className="of-card of-card-p6">
        <div className="mb-4 flex items-center justify-between gap-4">
          <h2 className="text-xl font-semibold">
            משתמשים בארגון
          </h2>
          <span className="text-sm text-zinc-500">
            {users.length} משתמשים
          </span>
        </div>

        {error ? (
          <div className="mb-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
            {error}
          </div>
        ) : null}

        {loading ? (
          <p className="text-sm text-zinc-500">טוען משתמשים...</p>
        ) : users.length === 0 ? (
          <p className="text-sm text-zinc-500">
            עדיין לא הוזמנו משתמשים לארגון.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-200 text-right dark:border-zinc-700">
                  <th className="px-3 py-3 font-semibold">שם</th>
                  <th className="px-3 py-3 font-semibold">אימייל</th>
                  <th className="px-3 py-3 font-semibold">תפקיד</th>
                  <th className="px-3 py-3 font-semibold">סטטוס</th>
                  <th className="px-3 py-3 font-semibold">פעולות</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr
                    key={user.id}
                    className="border-b border-zinc-100 dark:border-zinc-800"
                  >
                    <td className="px-3 py-3">
                      {user.full_name || "—"}
                    </td>
                    <td className="px-3 py-3">{user.email}</td>
                    <td className="px-3 py-3">
                      <Badge>{getRoleLabel(user.role)}</Badge>
                    </td>
                    <td className="px-3 py-3">
                      <Badge>
                        {user.account_status === "active"
                          ? "פעיל"
                          : "ממתין להגדרה"}
                      </Badge>
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex flex-wrap gap-2">
                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          disabled={
                            resendingUserId === user.id
                            || user.account_status === "active"
                          }
                          onClick={() => void handleResendInvite(user)}
                        >
                          {resendingUserId === user.id
                            ? "שולח..."
                            : "שליחת הזמנה מחדש"}
                        </Button>

                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          disabled={resettingUserId === user.id}
                          onClick={() => void handlePasswordReset(user)}
                        >
                          {resettingUserId === user.id
                            ? "שולח..."
                            : "איפוס סיסמה"}
                        </Button>

                        <Button
                          type="button"
                          variant="danger"
                          size="sm"
                          disabled={
                            deletingUserId === user.id
                            || user.id === profile?.id
                          }
                          onClick={() => void handleDelete(user)}
                        >
                          {user.id === profile?.id
                            ? "המשתמש שלך"
                            : deletingUserId === user.id
                              ? "מוחק..."
                              : "מחיקה"}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
