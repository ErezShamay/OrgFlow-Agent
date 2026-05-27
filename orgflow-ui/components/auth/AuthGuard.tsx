"use client";

import {
  useEffect,
} from "react";

import {
  usePathname,
  useRouter,
} from "next/navigation";

import {
  useAuth,
} from "@/contexts/AuthContext";

export default function AuthGuard({
  children,
}: {
  children: React.ReactNode;
}) {

  const {
    user,
    loading,
  } = useAuth();

  const router =
    useRouter();

  const pathname =
    usePathname();

  useEffect(() => {

    if (loading) {
      return;
    }

    const isAuthPage =
      pathname.startsWith(
        "/auth"
      );

    // ==========================
    // NOT AUTHENTICATED
    // ==========================

    if (
      !user
      && !isAuthPage
    ) {

      router.push(
        "/auth/login"
      );

      return;
    }

    // ==========================
    // ALREADY AUTHENTICATED
    // ==========================

    if (
      user
      && isAuthPage
    ) {

      router.push(
        "/portfolio"
      );
    }

  }, [

    user,
    loading,
    pathname,
    router,
  ]);

  // ==========================
  // LOADING
  // ==========================

  if (loading) {

    return (

      <main
        className="
          min-h-screen
          flex
          items-center
          justify-center
          bg-zinc-100
          dark:bg-zinc-950
        "
      >

        <div
          className="
            text-xl
            font-semibold
          "
        >
          טוען...
        </div>

      </main>

    );
  }

  // ==========================
  // BLOCK UNAUTHENTICATED
  // ==========================

  const isAuthPage =
    pathname.startsWith(
      "/auth"
    );

  if (
    !user
    && !isAuthPage
  ) {

    return null;
  }

  // ==========================
  // BLOCK AUTH PAGES
  // ==========================

  if (
    user
    && isAuthPage
  ) {

    return null;
  }

  return <>{children}</>;
}