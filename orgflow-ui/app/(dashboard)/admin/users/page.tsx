"use client";

import {
  FormEvent,
  useEffect,
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

export default function AdminUsersPage() {
  return (
    <AdminGuard>
      <AdminUsersContent />
    </AdminGuard>
  );
}

function AdminUsersContent() {
  const { profile, organizations, currentOrgId, sessionRole } = useAuth();
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const canManageOrganizations = useCanManageOrganizations();
  const effectiveRole = profile?.role || sessionRole;
  const hasClientAdmin = organizationHasClientAdmin(users);
  const roleOptions: Array<"ADMIN" | "SUPERVISOR" | "VIEWER"> = [
    ...inviteableRoles(effectiveRole, {
      hasClientAdmin,
    }),
  ];

  const [customerOrganizations, setCustomerOrganizations] =
    useState<CustomerOrganization[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [creatingOrganization, setCreatingOrganization] = useState(false);
  const [deletingUserId, setDeletingUserId] = useState<string | null>(null);
  const [resendingUserId, setResendingUserId] = useState<string | null>(null);
  const [resettingUserId, setResettingUserId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState<string>("VIEWER");
  const [organizationName, setOrganizationName] = useState("");
  const [organizationEmail, setOrganizationEmail] = useState("");

  useEffect(() => {
    if (
      roleOptions.length > 0
      && !roleOptions.includes(role as (typeof roleOptions)[number])
    ) {
      setRole(roleOptions[0]);
    }
  }, [roleOptions, role]);

  useEffect(() => {
    void loadUsers();
    void loadOrganizations();
  }, [currentOrgId]);

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
          role,
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
              value={role}
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
