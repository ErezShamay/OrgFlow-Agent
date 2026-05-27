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

import { supabase } from "@/lib/supabase";

type Profile = {

  id: string;

  email: string;

  full_name: string | null;

  role: string;
};

type AuthContextType = {

  user:
    User | null;

  session:
    Session | null;

  profile:
    Profile | null;

  loading:
    boolean;

  signOut:
    () => Promise<void>;
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

  const [
    user,
    setUser
  ] = useState<
    User | null
  >(null);

  const [
    session,
    setSession
  ] = useState<
    Session | null
  >(null);

  const [
    profile,
    setProfile
  ] = useState<
    Profile | null
  >(null);

  const [
    loading,
    setLoading
  ] = useState(true);

  useEffect(() => {

    loadSession();

    const {
      data: listener
    } = supabase.auth.onAuthStateChange(

      async (
        _event,
        session
      ) => {

        setSession(session);

        setUser(
          session?.user
          || null
        );

        if (
          session?.user
        ) {

          await loadProfile(
            session.user.id
          );

        } else {

          setProfile(null);
        }

        setLoading(false);
      }
    );

    return () => {

      listener.subscription.unsubscribe();

    };

  }, []);

  async function loadSession() {

    const {
      data,
    } = await supabase.auth.getSession();

    setSession(
      data.session
    );

    setUser(
      data.session?.user
      || null
    );

    if (
      data.session?.user
    ) {

      await loadProfile(
        data.session.user.id
      );
    }

    setLoading(false);
  }

  async function loadProfile(
    userId: string
  ) {

    try {

      const response =
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/profiles/${userId}`
        );

      if (!response.ok) {

        throw new Error(
          "Failed loading profile"
        );
      }

      const data =
        await response.json();

      setProfile(data);

    } catch (error) {

      console.error(error);
    }
  }

  async function signOut() {

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

  const context =
    useContext(AuthContext);

  if (!context) {

    throw new Error(
      "useAuth must be used inside AuthProvider"
    );
  }

  return context;
}