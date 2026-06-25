"use client";

import {
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { toast } from "sonner";

import AdminGuard from "@/components/admin/AdminGuard";
import DeleteOrganizationDialog from "@/components/admin/DeleteOrganizationDialog";
import { TenantMigrationBanner } from "@/components/admin/TenantMigrationBanner";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { useAuth } from "@/contexts/AuthContext";
import {
  useCanManageOrganizations,
} from "@/hooks/useEffectiveRole";
import {
  inviteableRoles,
  isPlatformAdmin,
  organizationHasClientAdmin,
} from "@/lib/auth/permissions";
import { isResidentRole } from "@/lib/auth/resident-access";
import { getRoleLabel } from "@/lib/auth/roleLabels";
import {
  inviteApartmentResident,
  listProjectApartments,
  updateProjectApartment,
} from "@/lib/apartments/api";
import type { ProjectApartment } from "@/lib/apartments/types";
import { apiFetch } from "@/lib/api/client";
import { normalizeProjectList } from "@/lib/api/read-error-message";
import { dispatchTenantManagerModuleChanged } from "@/lib/tenant-manager/module-events";
import { validateEmail, validateOptionalEmail } from "@/lib/validation/email";

const ALL_ORGANIZATIONS_SCOPE = "__all__";
const MAX_VISIBLE_USER_ROWS = 10;
const USER_LIST_ROW_REM = 3;
const USER_LIST_SCROLL_MAX_HEIGHT = `calc(${USER_LIST_ROW_REM}rem + ${MAX_VISIBLE_USER_ROWS} * ${USER_LIST_ROW_REM}rem)`;

const APARTMENT_INVITE_STATUS_LABELS: Record<string, string> = {
  none: "לא הוזמן",
  pending: "ממתין להפעלה",
  active: "פעיל",
};

type TenantProjectOption = {
  id: string;
  project_name: string;
};

type ManagedUser = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  organization_id?: string | null;
  organization_name?: string | null;
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

type TenantManagerModuleRow = {
  organization_id: string;
  organization_name: string;
  contact_email?: string;
  is_enabled: boolean;
};

type TenantManagerModulesResponse = {
  organizations: TenantManagerModuleRow[];
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
  const {
    profile,
    currentOrgId,
    sessionRole,
    refreshOrganizations,
    switchOrganization,
  } = useAuth();
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const canManageOrganizations = useCanManageOrganizations();
  const effectiveRole = profile?.role || sessionRole;
  const [customerOrganizations, setCustomerOrganizations] =
    useState<CustomerOrganization[]>([]);
  const [fieldReportModules, setFieldReportModules] = useState<
    FieldReportModuleRow[]
  >([]);
  const [fieldReportStorageAvailable, setFieldReportStorageAvailable] =
    useState(true);
  const [tenantManagerModules, setTenantManagerModules] = useState<
    TenantManagerModuleRow[]
  >([]);
  const [tenantManagerStorageAvailable, setTenantManagerStorageAvailable] =
    useState(true);
  const [togglingModuleOrgId, setTogglingModuleOrgId] = useState<
    string | null
  >(null);
  const [togglingTenantManagerOrgId, setTogglingTenantManagerOrgId] =
    useState<string | null>(null);
  const [exportingReportsOrgId, setExportingReportsOrgId] = useState<
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
  const [showCreateOrganizationForm, setShowCreateOrganizationForm] =
    useState(false);
  const [showInviteUserForm, setShowInviteUserForm] = useState(false);
  const [deletingOrganizationId, setDeletingOrganizationId] = useState<
    string | null
  >(null);
  const [organizationPendingDelete, setOrganizationPendingDelete] =
    useState<CustomerOrganization | null>(null);
  const [deleteOrganizationConfirmValue, setDeleteOrganizationConfirmValue] =
    useState("");
  const [deletingUserId, setDeletingUserId] = useState<string | null>(null);
  const [resendingUserId, setResendingUserId] = useState<string | null>(null);
  const [resettingUserId, setResettingUserId] = useState<string | null>(null);
  const [updatingUserId, setUpdatingUserId] = useState<string | null>(null);
  const [settingPasswordUserId, setSettingPasswordUserId] = useState<
    string | null
  >(null);
  const [usersScopeId, setUsersScopeId] = useState(ALL_ORGANIZATIONS_SCOPE);
  const [tenantProjects, setTenantProjects] = useState<TenantProjectOption[]>(
    []
  );
  const [selectedTenantProjectId, setSelectedTenantProjectId] = useState("");
  const [projectApartments, setProjectApartments] = useState<ProjectApartment[]>(
    []
  );
  const [loadingTenantProjects, setLoadingTenantProjects] = useState(false);
  const [loadingProjectApartments, setLoadingProjectApartments] =
    useState(false);
  const [updatingApartmentId, setUpdatingApartmentId] = useState<string | null>(
    null
  );
  const [invitingApartmentId, setInvitingApartmentId] = useState<string | null>(
    null
  );
  const [error, setError] = useState("");

  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [organizationName, setOrganizationName] = useState("");
  const [organizationEmail, setOrganizationEmail] = useState("");
  const [inviteOrganizationId, setInviteOrganizationId] = useState("");
  const [role, setRole] = useState<string>("VIEWER");

  const defaultInviteOrganizationId =
    canManageOrganizations
    && currentOrgId
    && customerOrganizations.some(
      (organization) => organization.id === currentOrgId
    )
      ? currentOrgId
      : "";

  const activeInviteOrganizationId =
    inviteOrganizationId || defaultInviteOrganizationId || "";

  const usersInInviteOrg = useMemo(
    () =>
      users.filter(
        (item) =>
          !activeInviteOrganizationId
          || item.organization_id === activeInviteOrganizationId
      ),
    [users, activeInviteOrganizationId]
  );
  const hasClientAdmin = organizationHasClientAdmin(usersInInviteOrg);
  const updateRoleOptions = useMemo(
    () =>
      isPlatformAdmin(effectiveRole)
        ? (["ADMIN", "SUPERVISOR", "DEVELOPER", "CONTRACTOR", "VIEWER"] as const)
        : (["SUPERVISOR", "DEVELOPER", "CONTRACTOR", "VIEWER"] as const),
    [effectiveRole]
  );
  const roleOptions = useMemo(
    () => [
      ...inviteableRoles(effectiveRole, {
        hasClientAdmin,
      }),
    ] as Array<
      "ADMIN" | "SUPERVISOR" | "DEVELOPER" | "CONTRACTOR" | "VIEWER"
    >,
    [effectiveRole, hasClientAdmin],
  );
  const selectedRole = roleOptions.includes(
    role as (typeof roleOptions)[number]
  )
    ? role
    : (roleOptions[0] ?? "VIEWER");

  const activeUsersScopeId = canManageOrganizations
    ? usersScopeId
    : "";

  const employeeUsers = useMemo(
    () => users.filter((user) => !isResidentRole(user.role)),
    [users]
  );

  const showOrganizationColumn =
    canManageOrganizations
    && activeUsersScopeId === ALL_ORGANIZATIONS_SCOPE;

  const loadTenantProjects = useCallback(async () => {
    try {
      setLoadingTenantProjects(true);
      const response = await apiFetch("/projects");

      if (!response.ok) {
        setTenantProjects([]);
        return;
      }

      const data = await response.json();
      const items = normalizeProjectList(data);
      setTenantProjects(items);
      setSelectedTenantProjectId((current) => {
        if (current && items.some((project) => project.id === current)) {
          return current;
        }

        return items.length === 1 ? items[0]!.id : "";
      });
    } catch {
      setTenantProjects([]);
    } finally {
      setLoadingTenantProjects(false);
    }
  }, []);

  const loadProjectApartments = useCallback(async (projectId: string) => {
    if (!projectId) {
      setProjectApartments([]);
      return;
    }

    try {
      setLoadingProjectApartments(true);
      const apartments = await listProjectApartments(projectId);
      setProjectApartments(apartments);
    } catch {
      setProjectApartments([]);
    } finally {
      setLoadingProjectApartments(false);
    }
  }, []);

  function adminUserActionQuery(
    user?: ManagedUser
  ) {
    const organizationId = user?.organization_id
      || (
        canManageOrganizations
        && activeUsersScopeId
        && activeUsersScopeId !== ALL_ORGANIZATIONS_SCOPE
          ? activeUsersScopeId
          : ""
      );

    if (!organizationId) {
      return "";
    }

    return `?organization_id=${encodeURIComponent(organizationId)}`;
  }

  function apartmentToManagedUser(
    apartment: ProjectApartment
  ): ManagedUser | null {
    if (!apartment.resident_profile_id) {
      return null;
    }

    const linkedUser = users.find(
      (user) => user.id === apartment.resident_profile_id
    );

    if (linkedUser) {
      return linkedUser;
    }

    return {
      id: apartment.resident_profile_id,
      email: apartment.email || "",
      full_name: apartment.owner_name,
      role: "RESIDENT",
      organization_id: apartment.organization_id,
      account_status:
        apartment.invite_status === "active" ? "active" : "pending",
    };
  }

  async function reloadSelectedProjectApartments() {
    if (!selectedTenantProjectId) {
      return;
    }

    await loadProjectApartments(selectedTenantProjectId);
  }

  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const usersPath = canManageOrganizations
        ? `/admin/users?organization_id=${encodeURIComponent(
            activeUsersScopeId || ALL_ORGANIZATIONS_SCOPE
          )}`
        : "/admin/users";

      const response = await apiFetch(usersPath);

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
  }, [activeUsersScopeId, canManageOrganizations]);

  useEffect(() => {
    let cancelled = false;

    queueMicrotask(() => {
      if (cancelled) {
        return;
      }

      void loadUsers();
      void loadOrganizations();
      if (canManageOrganizations) {
        void loadFieldReportModules();
        void loadTenantManagerModules();
      }
    });

    return () => {
      cancelled = true;
    };
  }, [
    currentOrgId,
    canManageOrganizations,
    activeUsersScopeId,
    loadUsers,
  ]);

  useEffect(() => {
    void loadTenantProjects();
  }, [currentOrgId, loadTenantProjects]);

  useEffect(() => {
    if (!selectedTenantProjectId) {
      setProjectApartments([]);
      return;
    }

    void loadProjectApartments(selectedTenantProjectId);
  }, [selectedTenantProjectId, loadProjectApartments]);

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

  async function loadTenantManagerModules() {
    try {
      const response = await apiFetch("/admin/tenant-manager/modules");

      if (!response.ok) {
        return;
      }

      const data = (await response.json()) as TenantManagerModulesResponse;
      setTenantManagerModules(data.organizations || []);
      setTenantManagerStorageAvailable(
        data.storage_available !== false
      );
    } catch {
      setTenantManagerModules([]);
    }
  }

  async function handleToggleTenantManagerModule(
    organizationId: string,
    nextEnabled: boolean
  ) {
    try {
      setTogglingTenantManagerOrgId(organizationId);
      setError("");

      const response = await apiFetch(
        `/admin/tenant-manager/modules/${organizationId}`,
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
          || "עדכון מודול מנהל דיירים נכשל"
        );
      }

      toast.success(
        nextEnabled
          ? "מודול מנהל דיירים הופעל"
          : "מודול מנהל דיירים כובה"
      );
      dispatchTenantManagerModuleChanged(organizationId);
      await loadTenantManagerModules();
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "עדכון מודול מנהל דיירים נכשל";
      setError(message);
      toast.error(message);
    } finally {
      setTogglingTenantManagerOrgId(null);
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

  async function handleExportFieldReports(
    organizationId: string,
    organizationName: string
  ) {
    try {
      setExportingReportsOrgId(organizationId);
      setError("");

      const response = await apiFetch(
        `/admin/field-reports/organizations/${organizationId}/export`
      );

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(
          data?.error?.message
          || data?.detail
          || "ייצוא הדוחות נכשל"
        );
      }

      const blob = await response.blob();
      const disposition = response.headers.get("Content-Disposition");
      const filenameMatch = disposition?.match(
        /filename\*=UTF-8''([^;]+)|filename="([^"]+)"/i
      );
      const encodedFilename = filenameMatch?.[1] || filenameMatch?.[2];
      const downloadName = encodedFilename
        ? decodeURIComponent(encodedFilename)
        : `field-reports_${organizationName}.zip`;

      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = downloadName;
      link.click();
      URL.revokeObjectURL(objectUrl);

      toast.success("הורדת הדוחות החלה");
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "ייצוא הדוחות נכשל";
      setError(message);
      toast.error(message);
    } finally {
      setExportingReportsOrgId(null);
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

  function organizationDisplayName(
    organization: CustomerOrganization
  ) {
    return (
      organization.organization_name
      || organization.name
      || organization.contact_email
      || organization.id
    );
  }

  function openDeleteOrganizationDialog(
    organization: CustomerOrganization
  ) {
    setOrganizationPendingDelete(organization);
    setDeleteOrganizationConfirmValue("");
  }

  function closeDeleteOrganizationDialog() {
    if (deletingOrganizationId) {
      return;
    }

    setOrganizationPendingDelete(null);
    setDeleteOrganizationConfirmValue("");
  }

  async function executeDeleteOrganization(
    organization: CustomerOrganization
  ) {
    const requiredName = organizationDisplayName(organization).trim();

    if (deleteOrganizationConfirmValue.trim() !== requiredName) {
      toast.error("יש להקליד את שם הלקוח בדיוק כפי שמוצג");
      return;
    }

    try {
      setDeletingOrganizationId(organization.id);
      setError("");

      const response = await apiFetch(
        `/admin/organizations/${organization.id}`,
        { method: "DELETE" }
      );
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data?.error?.message
          || data?.detail
          || "מחיקת הלקוח נכשלה"
        );
      }

      toast.success("הלקוח נמחק מהמערכת");

      const remainingOrganizations = customerOrganizations.filter(
        (item) => item.id !== organization.id
      );

      setCustomerOrganizations(remainingOrganizations);

      await Promise.all([
        loadOrganizations(),
        refreshOrganizations(),
        loadFieldReportModules(),
        loadTenantManagerModules(),
      ]);

      if (
        currentOrgId === organization.id
        && remainingOrganizations[0]?.id
      ) {
        await switchOrganization(remainingOrganizations[0].id);
        toast.info("עברת ללקוח אחר לאחר המחיקה");
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "מחיקת הלקוח נכשלה";
      setError(message);
      toast.error(message);
    } finally {
      setDeletingOrganizationId(null);
      setOrganizationPendingDelete(null);
      setDeleteOrganizationConfirmValue("");
    }
  }

  async function handleCreateOrganization(e: FormEvent) {
    e.preventDefault();

    const emailError = validateEmail(organizationEmail);
    if (emailError) {
      setError(emailError);
      toast.error(emailError);
      return;
    }

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
      setShowCreateOrganizationForm(false);

      const createdOrgId = String(
        data?.organization?.id || ""
      ).trim();

      await Promise.all([
        loadOrganizations(),
        refreshOrganizations(),
      ]);

      if (createdOrgId) {
        setInviteOrganizationId(createdOrgId);
        await switchOrganization(createdOrgId);
        toast.info(
          "עברת ללקוח החדש - ההזמנות הבאות ישויכו אליו"
        );
      }
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

    const emailError = validateEmail(email);
    if (emailError) {
      setError(emailError);
      toast.error(emailError);
      return;
    }

    try {
      setSubmitting(true);
      setError("");

      if (
        canManageOrganizations
        && !activeInviteOrganizationId
      ) {
        throw new Error("בחר לקוח לפני שליחת ההזמנה");
      }

      const response = await apiFetch("/admin/users", {
        method: "POST",
        body: JSON.stringify({
          email,
          full_name: fullName,
          role: selectedRole,
          ...(canManageOrganizations
            && activeInviteOrganizationId
            ? {
                organization_id: activeInviteOrganizationId,
              }
            : {}),
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
      setShowInviteUserForm(false);
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
        `/admin/users/${user.id}/resend-invite${adminUserActionQuery(user)}`,
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
        `/admin/users/${user.id}/password-reset${adminUserActionQuery(user)}`,
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

  async function handleUpdateUser(user: ManagedUser) {
    const nextName = window.prompt(
      "שם מלא",
      user.full_name || ""
    );

    if (nextName === null) {
      return;
    }

    const trimmedName = nextName.trim();
    if (!trimmedName) {
      toast.error("שם מלא הוא שדה חובה");
      return;
    }

    const nextRole = window.prompt(
      `תפקיד (${updateRoleOptions.join(", ")})`,
      user.role
    );

    if (nextRole === null) {
      return;
    }

    const normalizedRole = nextRole.trim().toUpperCase();
    if (!updateRoleOptions.some((option) => option === normalizedRole)) {
      toast.error("תפקיד לא חוקי");
      return;
    }

    const organizationQuery = adminUserActionQuery(user);
    if (canManageOrganizations && !organizationQuery) {
      toast.error("לא ניתן לעדכן משתמש ללא זיהוי לקוח");
      return;
    }

    try {
      setUpdatingUserId(user.id);
      setError("");

      const response = await apiFetch(
        `/admin/users/${user.id}${organizationQuery}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            full_name: trimmedName,
            role: normalizedRole,
          }),
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data?.error?.message
          || data?.detail
          || "עדכון המשתמש נכשל"
        );
      }

      toast.success("המשתמש עודכן");
      await loadUsers();
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "עדכון המשתמש נכשל";
      setError(message);
      toast.error(message);
    } finally {
      setUpdatingUserId(null);
    }
  }

  async function handleSetPassword(user: ManagedUser) {
    const organizationQuery = adminUserActionQuery(user);
    if (canManageOrganizations && !organizationQuery) {
      toast.error("לא ניתן להגדיר סיסמה ללא זיהוי לקוח");
      return;
    }

    const password = window.prompt(
      `הגדרת סיסמה חדשה עבור ${user.full_name || user.email}\n(לפחות 8 תווים, אות גדולה/קטנה, ספרה ותו מיוחד)`
    );

    if (!password) {
      return;
    }

    try {
      setSettingPasswordUserId(user.id);
      setError("");

      const response = await apiFetch(
        `/admin/users/${user.id}/set-password${organizationQuery}`,
        {
          method: "POST",
          body: JSON.stringify({ password }),
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const policyErrors = data?.error?.details?.errors;
        throw new Error(
          Array.isArray(policyErrors) && policyErrors.length > 0
            ? policyErrors.join("\n")
            : data?.error?.message
            || data?.detail
            || "הגדרת הסיסמה נכשלה"
        );
      }

      toast.success("הסיסמה עודכנה במערכת");
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "הגדרת הסיסמה נכשלה";
      setError(message);
      toast.error(message);
    } finally {
      setSettingPasswordUserId(null);
    }
  }

  async function handleEditApartment(apartment: ProjectApartment) {
    if (!selectedTenantProjectId) {
      return;
    }

    const nextOwnerName = window.prompt(
      "שם דייר",
      apartment.owner_name || ""
    );

    if (nextOwnerName === null) {
      return;
    }

    const trimmedOwnerName = nextOwnerName.trim();
    if (!trimmedOwnerName) {
      toast.error("שם דייר הוא שדה חובה");
      return;
    }

    const nextEmail = window.prompt(
      "אימייל",
      apartment.email || ""
    );

    if (nextEmail === null) {
      return;
    }

    const emailError = validateOptionalEmail(nextEmail);
    if (emailError) {
      toast.error(emailError);
      return;
    }

    const nextPhone = window.prompt(
      "טלפון",
      apartment.phone || ""
    );

    if (nextPhone === null) {
      return;
    }

    try {
      setUpdatingApartmentId(apartment.id);
      setError("");

      await updateProjectApartment(
        selectedTenantProjectId,
        apartment.id,
        {
          apartment_number: apartment.apartment_number,
          owner_name: trimmedOwnerName,
          phone: nextPhone.trim() || null,
          email: nextEmail.trim() || null,
        }
      );

      toast.success("פרטי הדייר עודכנו");
      await reloadSelectedProjectApartments();
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "עדכון פרטי הדייר נכשל";
      setError(message);
      toast.error(message);
    } finally {
      setUpdatingApartmentId(null);
    }
  }

  async function handleInviteApartment(apartment: ProjectApartment) {
    if (!selectedTenantProjectId) {
      return;
    }

    if (!apartment.email?.trim()) {
      toast.error("נדרש מייל לדייר לפני שליחת הזמנה");
      return;
    }

    try {
      setInvitingApartmentId(apartment.id);
      setError("");

      await inviteApartmentResident(
        selectedTenantProjectId,
        apartment.id
      );

      toast.success("הזמנה נשלחה לדייר");
      await reloadSelectedProjectApartments();
      await loadUsers();
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "שליחת ההזמנה נכשלה";
      setError(message);
      toast.error(message);
    } finally {
      setInvitingApartmentId(null);
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
        `/admin/users/${user.id}${adminUserActionQuery(user)}`,
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
      if (isResidentRole(user.role)) {
        await reloadSelectedProjectApartments();
      }
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

  const pendingDeleteConfirmName = organizationPendingDelete
    ? organizationDisplayName(organizationPendingDelete)
    : "";

  return (
    <div className="of-dashboard-page of-container mx-auto max-w-5xl space-y-10">
      <DeleteOrganizationDialog
        open={organizationPendingDelete !== null}
        organizationLabel={
          organizationPendingDelete
            ? organizationDisplayName(organizationPendingDelete)
            : ""
        }
        confirmName={pendingDeleteConfirmName}
        confirmValue={deleteOrganizationConfirmValue}
        deleting={
          organizationPendingDelete !== null
          && deletingOrganizationId === organizationPendingDelete.id
        }
        onConfirmValueChange={setDeleteOrganizationConfirmValue}
        onCancel={closeDeleteOrganizationDialog}
        onConfirm={() => {
          if (!organizationPendingDelete) {
            return;
          }

          void executeDeleteOrganization(organizationPendingDelete);
        }}
      />

      <header>
        <h1 className="of-page-title text-2xl md:text-3xl">
          ניהול משתמשים
        </h1>
        <p className="of-page-desc max-w-2xl text-sm">
          {canManageOrganizations
            ? "אתה מנהל גלובלי - גישה לכל הלקוחות, יצירת לקוחות חדשים, וניהול משתמשים בכל חברה."
            : "אתה מנהל לקוח - ניהול משתמשים ופעולות רק עבור הלקוח הפעיל."}
        </p>
      </header>

      {canManageOrganizations ? <TenantMigrationBanner /> : null}

      {canManageOrganizations ? (
      <section className="of-card of-card-p6">
        <h2 className="mb-4 text-xl font-semibold">
          לקוחות במערכת
        </h2>

        {showCreateOrganizationForm ? (
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

            <div className="md:col-span-2 flex flex-wrap gap-2">
              <Button
                type="submit"
                variant="accent"
                disabled={creatingOrganization}
              >
                {creatingOrganization ? "יוצר לקוח..." : "יצירת לקוח"}
              </Button>
              <Button
                type="button"
                variant="secondary"
                disabled={creatingOrganization}
                onClick={() => {
                  setShowCreateOrganizationForm(false);
                  setOrganizationName("");
                  setOrganizationEmail("");
                }}
              >
                ביטול
              </Button>
            </div>
          </form>
        ) : (
          <div className="mb-6">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowCreateOrganizationForm(true)}
            >
              הוספת לקוח חדש
            </Button>
          </div>
        )}

        {customerOrganizations.length > 0 ? (
          <ul className="space-y-2 text-sm">
            {customerOrganizations.map((organization) => (
              <li
                key={organization.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-zinc-200/80 px-4 py-3 dark:border-zinc-800"
              >
                <span className="font-medium">
                  {organizationDisplayName(organization)}
                </span>
                <span className="text-zinc-500">
                  {organization.contact_email || organization.id}
                </span>
                <div className="flex flex-wrap items-center gap-2">
                  {organization.id === currentOrgId ? (
                    <Badge>לקוח פעיל</Badge>
                  ) : null}
                  <Button
                    type="button"
                    variant="danger"
                    size="sm"
                    disabled={deletingOrganizationId === organization.id}
                    onClick={() =>
                      openDeleteOrganizationDialog(organization)
                    }
                  >
                    {deletingOrganizationId === organization.id
                      ? "מוחק..."
                      : "מחיקת לקוח"}
                  </Button>
                </div>
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
            מודול הפקת דוחות
          </h3>
          <p className="mb-4 text-sm text-zinc-500">
            הפעלה וכיבוי לפי ארגון. ארגון ללא מודול לא יכול לגשת לאזור
            «הפקת דוחות».
          </p>

          {!fieldReportStorageAvailable ? (
            <p className="mb-4 text-sm text-amber-700 dark:text-amber-400">
              טבלאות המודול אינן קיימות במסד - יש להריץ את המיגרציות
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
                          לביקורת.
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
                      <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        disabled={
                          !fieldReportStorageAvailable
                          || exportingReportsOrgId === row.organization_id
                        }
                        onClick={() =>
                          void handleExportFieldReports(
                            row.organization_id,
                            row.organization_name
                          )
                        }
                      >
                        {exportingReportsOrgId === row.organization_id
                          ? "מוריד..."
                          : "הורדת כל הדוחות"}
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

        <div className="mt-10 border-t border-zinc-200/80 pt-8 dark:border-zinc-800">
          <h3 className="mb-2 text-lg font-semibold">
            מודול מנהל דיירים
          </h3>
          <p className="mb-4 text-sm text-zinc-500">
            הפעלה וכיבוי לפי לקוח. מופיע תחת «כלים נוספים» בניווט כשמופעל.
          </p>

          {!tenantManagerStorageAvailable ? (
            <p className="mb-4 text-sm text-amber-700 dark:text-amber-400">
              טבלאות המודול אינן קיימות במסד - יש להריץ את המיגרציה
              2026061101_organization_tenant_manager_module.sql
            </p>
          ) : null}

          {tenantManagerModules.length > 0 ? (
            <ul className="space-y-2 text-sm">
              {tenantManagerModules.map((row) => (
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
                          !tenantManagerStorageAvailable
                          || togglingTenantManagerOrgId === row.organization_id
                        }
                        onClick={() =>
                          void handleToggleTenantManagerModule(
                            row.organization_id,
                            !row.is_enabled
                          )
                        }
                      >
                        {togglingTenantManagerOrgId === row.organization_id
                          ? "מעדכן..."
                          : row.is_enabled
                            ? "כיבוי"
                            : "הפעלה"}
                      </Button>
                    </div>
                  </div>
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
        <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">עובדי החברה</h2>
            <p className="mt-1 text-sm text-zinc-500">
              {employeeUsers.length} עובדים
            </p>
          </div>
          {!showInviteUserForm ? (
            <Button
              type="button"
              variant="accent"
              onClick={() => setShowInviteUserForm(true)}
            >
              משתמש חדש
            </Button>
          ) : null}
        </div>

        {canManageOrganizations ? (
          <div className="mb-4">
            <label className="mb-2 block text-sm font-medium">
              תצוגת משתמשים
            </label>
            <select
              value={activeUsersScopeId}
              onChange={(event) => {
                setUsersScopeId(event.target.value);
              }}
              className="of-input of-focus-ring w-full max-w-md text-sm"
            >
              <option value={ALL_ORGANIZATIONS_SCOPE}>
                כל המשתמשים במערכת
              </option>
              {customerOrganizations.map((organization) => (
                <option
                  key={organization.id}
                  value={organization.id}
                >
                  {organizationDisplayName(organization)}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        {showInviteUserForm ? (
          <div className="mb-6 rounded-2xl border border-zinc-200/80 bg-zinc-50/80 p-5 dark:border-zinc-800 dark:bg-zinc-900/40">
            <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold">
                  {canManageOrganizations
                    ? "הזמנת משתמש ללקוח"
                    : "הזמנת משתמש לחברה"}
                </h3>
                <p className="mt-1 text-sm text-zinc-500">
                  {canManageOrganizations
                    ? "בחרו במפורש לאיזה לקוח משויך המשתמש."
                    : "משתמשים חדשים ישויכו לחברה שלך בלבד."}
                  {" "}
                  לכל לקוח מותר מנהל לקוח אחד בלבד.
                  {hasClientAdmin && canManageOrganizations
                    ? " ללקוח שנבחר כבר יש מנהל לקוח - ניתן להזמין מפקח או משתמש כללי."
                    : ""}
                </p>
              </div>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={submitting}
                onClick={() => {
                  setShowInviteUserForm(false);
                  setEmail("");
                  setFullName("");
                  setRole("VIEWER");
                }}
              >
                ביטול
              </Button>
            </div>

            <form
              onSubmit={handleInvite}
              className="grid gap-4 md:grid-cols-2"
            >
              {canManageOrganizations ? (
                <div className="md:col-span-2">
                  <label className="mb-2 block text-sm font-medium">
                    לקוח
                  </label>
                  <select
                    value={activeInviteOrganizationId}
                    onChange={(event) => {
                      setInviteOrganizationId(event.target.value);
                    }}
                    required
                    className="of-input of-focus-ring w-full text-sm"
                  >
                    <option value="" disabled>
                      בחר לקוח
                    </option>
                    {customerOrganizations.map((organization) => (
                      <option
                        key={organization.id}
                        value={organization.id}
                      >
                        {organization.organization_name
                          || organization.name
                          || organization.contact_email
                          || organization.id}
                      </option>
                    ))}
                  </select>
                </div>
              ) : null}

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
          </div>
        ) : null}

        {error ? (
          <div className="mb-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
            {error}
          </div>
        ) : null}

        {loading ? (
          <p className="text-sm text-zinc-500">טוען משתמשים...</p>
        ) : employeeUsers.length === 0 ? (
          <p className="text-sm text-zinc-500">
            עדיין לא הוזמנו עובדים לארגון.
          </p>
        ) : (
          <div
            className="overflow-x-auto overflow-y-auto"
            style={{ maxHeight: USER_LIST_SCROLL_MAX_HEIGHT }}
          >
            <table className="min-w-full text-sm">
              <thead className="sticky top-0 z-10 bg-[var(--of-color-surface)]">
                <tr className="border-b border-zinc-200 text-right dark:border-zinc-700">
                  <th className="px-3 py-3 font-semibold">שם</th>
                  <th className="px-3 py-3 font-semibold">אימייל</th>
                  {showOrganizationColumn ? (
                    <th className="px-3 py-3 font-semibold">לקוח</th>
                  ) : null}
                  <th className="px-3 py-3 font-semibold">תפקיד</th>
                  <th className="px-3 py-3 font-semibold">סטטוס</th>
                  <th className="px-3 py-3 font-semibold">פעולות</th>
                </tr>
              </thead>
              <tbody>
                {employeeUsers.map((user) => (
                  <tr
                    key={user.id}
                    className="border-b border-zinc-100 dark:border-zinc-800"
                  >
                    <td className="px-3 py-3">
                      {user.full_name || "-"}
                    </td>
                    <td className="px-3 py-3">{user.email}</td>
                    {showOrganizationColumn ? (
                      <td className="px-3 py-3 text-zinc-600 dark:text-zinc-400">
                        {user.organization_name
                          || user.organization_id
                          || "-"}
                      </td>
                    ) : null}
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
                          disabled={updatingUserId === user.id}
                          onClick={() => void handleUpdateUser(user)}
                        >
                          {updatingUserId === user.id
                            ? "מעדכן..."
                            : "עריכה"}
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
                          variant="secondary"
                          size="sm"
                          disabled={settingPasswordUserId === user.id}
                          onClick={() => void handleSetPassword(user)}
                        >
                          {settingPasswordUserId === user.id
                            ? "מגדיר..."
                            : "הגדרת סיסמה"}
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

      <section className="of-card of-card-p6">
        <div className="mb-4">
          <h2 className="text-xl font-semibold">דיירים בפרויקט</h2>
          <p className="mt-1 text-sm text-zinc-500">
            {selectedTenantProjectId
              ? `${projectApartments.length} דיירים בפרויקט שנבחר`
              : "בחרו פרויקט כדי לראות את רשימת הדיירים"}
          </p>
        </div>

        <div className="mb-4">
          <label className="mb-2 block text-sm font-medium">פרויקט</label>
          <select
            value={selectedTenantProjectId}
            onChange={(event) => {
              setSelectedTenantProjectId(event.target.value);
            }}
            disabled={loadingTenantProjects || tenantProjects.length === 0}
            className="of-input of-focus-ring w-full max-w-md text-sm"
          >
            <option value="">
              {loadingTenantProjects
                ? "טוען פרויקטים..."
                : tenantProjects.length === 0
                  ? "אין פרויקטים זמינים"
                  : "בחר פרויקט"}
            </option>
            {tenantProjects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.project_name}
              </option>
            ))}
          </select>
        </div>

        {loadingProjectApartments ? (
          <p className="text-sm text-zinc-500">טוען דיירים...</p>
        ) : !selectedTenantProjectId ? (
          <p className="text-sm text-zinc-500">
            יש לבחור פרויקט כדי להציג את הדיירים.
          </p>
        ) : projectApartments.length === 0 ? (
          <p className="text-sm text-zinc-500">
            אין דיירים רשומים בפרויקט זה.
          </p>
        ) : (
          <div
            className="overflow-x-auto overflow-y-auto"
            style={{ maxHeight: USER_LIST_SCROLL_MAX_HEIGHT }}
          >
            <table className="min-w-full text-sm">
              <thead className="sticky top-0 z-10 bg-[var(--of-color-surface)]">
                <tr className="border-b border-zinc-200 text-right dark:border-zinc-700">
                  <th className="px-3 py-3 font-semibold">דירה</th>
                  <th className="px-3 py-3 font-semibold">שם</th>
                  <th className="px-3 py-3 font-semibold">אימייל</th>
                  <th className="px-3 py-3 font-semibold">טלפון</th>
                  <th className="px-3 py-3 font-semibold">חשבון</th>
                  <th className="px-3 py-3 font-semibold">פעולות</th>
                </tr>
              </thead>
              <tbody>
                {projectApartments.map((apartment) => {
                  const residentUser = apartmentToManagedUser(apartment);

                  return (
                  <tr
                    key={apartment.id}
                    className="border-b border-zinc-100 dark:border-zinc-800"
                  >
                    <td className="px-3 py-3" dir="ltr">
                      {apartment.apartment_number}
                    </td>
                    <td className="px-3 py-3">
                      {apartment.owner_name || "-"}
                    </td>
                    <td className="px-3 py-3">
                      {apartment.email || "-"}
                    </td>
                    <td className="px-3 py-3" dir="ltr">
                      {apartment.phone || "-"}
                    </td>
                    <td className="px-3 py-3">
                      <Badge>
                        {APARTMENT_INVITE_STATUS_LABELS[
                          apartment.invite_status
                        ] || apartment.invite_status}
                      </Badge>
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex flex-wrap gap-2">
                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          disabled={updatingApartmentId === apartment.id}
                          onClick={() => void handleEditApartment(apartment)}
                        >
                          {updatingApartmentId === apartment.id
                            ? "מעדכן..."
                            : "עריכה"}
                        </Button>

                        {residentUser ? (
                          <>
                            <Button
                              type="button"
                              variant="secondary"
                              size="sm"
                              disabled={
                                resendingUserId === residentUser.id
                                || residentUser.account_status === "active"
                              }
                              onClick={() =>
                                void handleResendInvite(residentUser)
                              }
                            >
                              {resendingUserId === residentUser.id
                                ? "שולח..."
                                : "שליחת הזמנה מחדש"}
                            </Button>

                            <Button
                              type="button"
                              variant="secondary"
                              size="sm"
                              disabled={resettingUserId === residentUser.id}
                              onClick={() =>
                                void handlePasswordReset(residentUser)
                              }
                            >
                              {resettingUserId === residentUser.id
                                ? "שולח..."
                                : "איפוס סיסמה"}
                            </Button>

                            <Button
                              type="button"
                              variant="secondary"
                              size="sm"
                              disabled={
                                settingPasswordUserId === residentUser.id
                              }
                              onClick={() =>
                                void handleSetPassword(residentUser)
                              }
                            >
                              {settingPasswordUserId === residentUser.id
                                ? "מגדיר..."
                                : "הגדרת סיסמה"}
                            </Button>

                            <Button
                              type="button"
                              variant="danger"
                              size="sm"
                              disabled={deletingUserId === residentUser.id}
                              onClick={() =>
                                void handleDelete(residentUser)
                              }
                            >
                              {deletingUserId === residentUser.id
                                ? "מוחק..."
                                : "מחיקה"}
                            </Button>
                          </>
                        ) : (
                          <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            disabled={
                              invitingApartmentId === apartment.id
                              || !apartment.email?.trim()
                            }
                            onClick={() =>
                              void handleInviteApartment(apartment)
                            }
                          >
                            {invitingApartmentId === apartment.id
                              ? "שולח..."
                              : "שליחת הזמנה"}
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
