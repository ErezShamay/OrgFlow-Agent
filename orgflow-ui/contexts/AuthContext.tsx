"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  User,
  Session,
} from "@supabase/supabase-js";

import {
  logAuthError,
  logAuthInfo,
  logAuthWarn,
} from "@/lib/auth/logger";
import {
  apiFetch,
  clearApiSession,
  exchangeBackendToken,
  getApiBaseUrl,
  ProfileLoadError,
  TokenExchangeError,
} from "@/lib/api/client";
import {
  assertFieldReportLogoutAllowed,
  FieldReportLogoutBlockedError,
  type FieldReportLogoutBlock,
} from "@/lib/field-reports/field-report-logout-block";
import { useIdleSessionTimeout } from "@/hooks/useIdleSessionTimeout";
import { supabase } from "@/lib/supabase";
import { toast } from "sonner";

type Profile = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  organization_id?: string | null;
};

type Project = {
  id: string;
  project_name: string;
  status: string;
};

type Organization = {
  id: string;
  organization_name?: string;
  name?: string;
  contact_email?: string;
  projects?: Project[];
};

type AuthContextType = {
  user: User | null;
  session: Session | null;
  profile: Profile | null;
  sessionRole: string | null;
  organizations: Organization[];
  currentOrgId: string | null;
  loading: boolean;
  authBootstrapError: string | null;
  switchOrganization: (organizationId: string) => Promise<void>;
  refreshOrganizations: () => Promise<void>;
  signOut: () => Promise<{ ok: true } | { ok: false; block: FieldReportLogoutBlock }>;
};

const AuthContext =
  createContext<
    AuthContextType | undefined
  >(undefined);

async function clearSupabaseSession() {
  clearApiSession();
  await supabase.auth.signOut();
}

function shouldSignOutAfterBootstrapError(error: unknown): boolean {
  if (error instanceof TokenExchangeError) {
    return [0, 401, 404, 422].includes(error.status);
  }

  if (error instanceof ProfileLoadError) {
    return [401, 403, 404].includes(error.status);
  }

  return false;
}

function bootstrapErrorMessage(error: unknown): string {
  if (error instanceof TokenExchangeError) {
    return error.status === 0
      ? `לא ניתן להגיע לשרת ב-${getApiBaseUrl()} — ודאו שה-API רץ (uvicorn --host 0.0.0.0) ושהמכשיר והמחשב באותה רשת`
      : `שגיאת שרת (${error.status}): ${error.message}`;
  }

  if (error instanceof ProfileLoadError) {
    return `טעינת פרופיל נכשלה (${error.status}): ${error.message}`;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "שגיאה בהתחברות לשרת";
}

export function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [sessionRole, setSessionRole] = useState<string | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentOrgId, setCurrentOrgId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [authBootstrapError, setAuthBootstrapError] = useState<string | null>(
    null
  );

  const FORCE_LOGIN =
    process.env.NEXT_PUBLIC_FORCE_LOGIN === "true";

  const loadProfile = useCallback(async (userId: string) => {
    const response = await apiFetch(`/profiles/${userId}`);

    if (!response.ok) {
      let message = `Failed loading profile (${response.status})`;

      try {
        const body = await response.json();
        message =
          body?.detail
          || body?.error?.message
          || message;
      } catch {
        // Keep default message when error body is not JSON.
      }

      throw new ProfileLoadError(message, response.status);
    }

    const data = await response.json();
    setProfile(data);
    logAuthInfo("profile:loaded", { userId });
  }, []);

  const loadOrganizations = useCallback(async () => {
    const response = await apiFetch("/auth/organizations");

    if (!response.ok) {
      setOrganizations([]);
      return;
    }

    const data = await response.json();
    const organizations = Array.isArray(data?.organizations)
      ? data.organizations
      : [];

    setOrganizations(
      organizations.map((organization: Organization) => ({
        ...organization,
        projects: organization.projects ?? [],
      }))
    );
  }, []);

  const establishBackendSession = useCallback(
    async (
      nextSession: Session,
      organizationId?: string | null,
    ) => {
      if (!nextSession.user) {
        return false;
      }

      logAuthInfo("bootstrap:start", {
        userId: nextSession.user.id,
        email: nextSession.user.email,
        organizationId: organizationId ?? null,
        apiBaseUrl: getApiBaseUrl(),
      });

      const exchangeData = await exchangeBackendToken(
        nextSession.user.id,
        organizationId,
      );

      const { data: refreshed, error: refreshError } =
        await supabase.auth.refreshSession();
      if (refreshError) {
        logAuthWarn("bootstrap:refresh_session_failed", {
          userId: nextSession.user.id,
          message: refreshError.message,
        });
      } else if (refreshed.session) {
        nextSession = refreshed.session;
      }

      setSessionRole(exchangeData.role || null);
      setCurrentOrgId(exchangeData.org_id || null);
      await loadProfile(nextSession.user.id);

      try {
        await loadOrganizations();
      } catch (error) {
        console.warn("Failed loading organizations:", error);
        setOrganizations([]);
      }

      setAuthBootstrapError(null);
      setSession(nextSession);
      setUser(nextSession.user);
      logAuthInfo("bootstrap:ok", {
        userId: nextSession.user.id,
        orgId: exchangeData.org_id,
        role: exchangeData.role,
      });
      return true;
    },
    [loadOrganizations, loadProfile]
  );

  const handleSession = useCallback(
    async (nextSession: Session | null) => {
      if (FORCE_LOGIN && nextSession?.user) {
        logAuthWarn("bootstrap:force_login", {
          userId: nextSession.user.id,
        });
        await clearSupabaseSession();
        setSession(null);
        setUser(null);
        setProfile(null);
        setSessionRole(null);
        setOrganizations([]);
        setCurrentOrgId(null);
        return;
      }

      if (!nextSession?.user) {
        logAuthInfo("bootstrap:signed_out");
        setAuthBootstrapError(null);
        clearApiSession();
        setSession(null);
        setUser(null);
        setProfile(null);
        setSessionRole(null);
        setOrganizations([]);
        setCurrentOrgId(null);
        return;
      }

      try {
        await establishBackendSession(nextSession);
      } catch (error) {
        const signOut = shouldSignOutAfterBootstrapError(error);

        logAuthError("bootstrap:failed", error, {
          userId: nextSession.user.id,
          email: nextSession.user.email,
          apiBaseUrl: getApiBaseUrl(),
          signOut,
        });

        clearApiSession();
        setSession(null);
        setUser(null);
        setProfile(null);
        setSessionRole(null);
        setOrganizations([]);
        setCurrentOrgId(null);
        setAuthBootstrapError(bootstrapErrorMessage(error));

        if (signOut) {
          await supabase.auth.signOut();
        }
      }
    },
    [FORCE_LOGIN, establishBackendSession]
  );

  const bootstrapInflightRef = useRef<{
    userId: string;
    promise: Promise<void>;
  } | null>(null);

  const runBootstrap = useCallback(
    async (nextSession: Session | null) => {
      const userId = nextSession?.user?.id ?? "";

      if (
        bootstrapInflightRef.current?.userId === userId
        && bootstrapInflightRef.current.promise
      ) {
        await bootstrapInflightRef.current.promise;
        return;
      }

      const promise = handleSession(nextSession);
      bootstrapInflightRef.current = { userId, promise };

      try {
        await promise;
      } finally {
        if (bootstrapInflightRef.current?.promise === promise) {
          bootstrapInflightRef.current = null;
        }
      }
    },
    [handleSession]
  );

  useEffect(() => {
    let active = true;

    const { data: listener } = supabase.auth.onAuthStateChange(
      (event, nextSession) => {
        if (!active) {
          return;
        }

        logAuthInfo("supabase:event", {
          event,
          userId: nextSession?.user?.id ?? null,
        });

        setLoading(true);

        void runBootstrap(nextSession).finally(() => {
          if (active) {
            setLoading(false);
          }
        });
      }
    );

    return () => {
      active = false;
      listener.subscription.unsubscribe();
    };
  }, [runBootstrap]);

  async function switchOrganization(organizationId: string) {
    if (!session?.user) {
      return;
    }

    await establishBackendSession(session, organizationId);
  }

  const signOut = useCallback(async () => {
    const organizationId = currentOrgId ?? profile?.organization_id ?? null;
    const userId = profile?.id ?? user?.id ?? null;

    try {
      await assertFieldReportLogoutAllowed(organizationId, userId);
    } catch (error: unknown) {
      if (error instanceof FieldReportLogoutBlockedError) {
        return { ok: false as const, block: error.block };
      }

      throw error;
    }

    await clearSupabaseSession();
    setSession(null);
    setUser(null);
    setProfile(null);
    setSessionRole(null);
    setOrganizations([]);
    setCurrentOrgId(null);
    return { ok: true as const };
  }, [currentOrgId, profile?.id, profile?.organization_id, user?.id]);

  useIdleSessionTimeout(Boolean(user) && !loading, async () => {
    const result = await signOut();
    if (!result.ok) {
      toast.warning(
        result.block?.message || "לא ניתן להתנתק — דוחות ממתינים לשליחה"
      );
      throw new Error("field-report-logout-blocked");
    }
  });

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        profile,
        sessionRole,
        organizations,
        currentOrgId,
        loading,
        authBootstrapError,
        switchOrganization,
        refreshOrganizations: loadOrganizations,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider"
    );
  }

  return context;
}
