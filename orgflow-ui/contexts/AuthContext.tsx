"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import {
  User,
  Session,
} from "@supabase/supabase-js";

import {
  apiFetch,
  clearApiSession,
  exchangeBackendToken,
} from "@/lib/api/client";
import { supabase } from "@/lib/supabase";

type Profile = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  organization_id?: string | null;
};

type AuthContextType = {
  user: User | null;
  session: Session | null;
  profile: Profile | null;
  loading: boolean;
  signOut: () => Promise<void>;
};

const AuthContext =
  createContext<
    AuthContextType | undefined
  >(undefined);

export function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  const FORCE_LOGIN =
    process.env.NEXT_PUBLIC_FORCE_LOGIN === "true";

  useEffect(() => {
    loadSession();

    const { data: listener } = supabase.auth.onAuthStateChange(
      async (_event, nextSession) => {
        setSession(nextSession);
        setUser(nextSession?.user || null);

        if (nextSession?.user) {
          await bootstrapBackendSession(nextSession.user.id);
        } else {
          clearApiSession();
          setProfile(null);
        }

        setLoading(false);
      }
    );

    return () => {
      listener.subscription.unsubscribe();
    };
  }, []);

  async function bootstrapBackendSession(userId: string) {
    try {
      await exchangeBackendToken(userId);
      await loadProfile(userId);
    } catch (error) {
      console.error("Failed bootstrapping backend session:", error);
      setProfile(null);
    }
  }

  async function loadSession() {
    const { data } = await supabase.auth.getSession();

    if (FORCE_LOGIN && data.session?.user) {
      await supabase.auth.signOut();
      clearApiSession();
      setSession(null);
      setUser(null);
      setProfile(null);
      setLoading(false);
      return;
    }

    setSession(data.session);
    setUser(data.session?.user || null);

    if (data.session?.user) {
      await bootstrapBackendSession(data.session.user.id);
    } else {
      clearApiSession();
    }

    setLoading(false);
  }

  async function loadProfile(userId: string) {
    try {
      const response = await apiFetch(`/profiles/${userId}`);

      if (!response.ok) {
        throw new Error("Failed loading profile");
      }

      const data = await response.json();
      setProfile(data);
    } catch (error) {
      console.error(error);
    }
  }

  async function signOut() {
    clearApiSession();
    await supabase.auth.signOut();
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        profile,
        loading,
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
