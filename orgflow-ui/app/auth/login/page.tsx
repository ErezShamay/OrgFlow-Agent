"use client";

import Link from "next/link";
import { Eye } from "lucide-react";

import {
  useEffect,
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";

import BrandLogo from "@/components/ui/BrandLogo";
import Button from "@/components/ui/Button";
import {
  useAuth,
} from "@/contexts/AuthContext";
import {
  logAuthError,
  logAuthInfo,
} from "@/lib/auth/logger";
import {
  describeMobileAuthConfig,
  getApiBaseUrl,
  isSupabaseConfigured,
} from "@/lib/env/public-env";
import { resolvePostLoginRoute } from "@/lib/navigation";
import { supabase } from "@/lib/supabase";

export default function LoginPage() {
  const router = useRouter();
  const {
    user,
    loading: authLoading,
    authBootstrapError,
    profile,
    sessionRole,
  } = useAuth();
  const configWarning = describeMobileAuthConfig();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordRevealed, setPasswordRevealed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [awaitingRedirect, setAwaitingRedirect] = useState(false);

  useEffect(() => {
    if (!awaitingRedirect) {
      return;
    }

    if (!authLoading && !user) {
      const message =
        authBootstrapError
        || configWarning
        || "לא ניתן להשלים את ההתחברות. נסו שוב.";

      logAuthError("login:redirect_failed", new Error(message), {
        authBootstrapError,
        configWarning,
        apiBaseUrl: getApiBaseUrl(),
      });

      setAwaitingRedirect(false);
      setLoading(false);
      setError(message);
      return;
    }

    if (authLoading || !user) {
      return;
    }

    const postLoginRoute = resolvePostLoginRoute(
      sessionRole || profile?.role
    );

    if (!sessionRole && !profile?.role) {
      return;
    }

    logAuthInfo("login:redirect_ok", {
      route: postLoginRoute,
      userId: user.id,
    });

    setAwaitingRedirect(false);
    setLoading(false);
    router.replace(postLoginRoute);
  }, [
    awaitingRedirect,
    authLoading,
    authBootstrapError,
    configWarning,
    router,
    user,
    profile?.role,
    sessionRole,
  ]);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();

    let redirectPending = false;

    try {
      setLoading(true);
      setError("");

      if (!isSupabaseConfigured()) {
        throw new Error(
          configWarning
          || "Supabase לא מוגדר - בנו APK עם .env.capacitor.local"
        );
      }

      logAuthInfo("login:supabase:start", {
        email,
        apiBaseUrl: getApiBaseUrl(),
      });

      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        throw error;
      }

      logAuthInfo("login:supabase:ok", { email });
      redirectPending = true;
      setAwaitingRedirect(true);
    } catch (err: unknown) {
      logAuthError("login:supabase:failed", err, {
        email,
        apiBaseUrl: getApiBaseUrl(),
      });

      setError(
        err instanceof Error
          ? err.message
          : "Login failed"
      );
    } finally {
      if (!redirectPending) {
        setLoading(false);
      }
    }
  }

  return (
    <main className="of-auth-page">
      <div
        className="
          pointer-events-none
          absolute
          inset-0
          overflow-hidden
        "
        aria-hidden
      >
        <div className="of-landing-orb of-landing-orb-1 absolute" />
        <div className="of-landing-orb of-landing-orb-2 absolute" />
      </div>

      <div className="of-auth-card of-animate-fade-up mx-auto w-full max-w-md">
        <div className="mb-8 flex justify-center">
          <BrandLogo size="lg" href="/" />
        </div>

        <div className="mb-8 text-center">
          <p className="mb-2 text-sm font-medium text-brand dark:text-brand-light">
            ברוכים השבים
          </p>
          <h1 className="text-3xl font-black tracking-tight">
            התחברות
          </h1>
          <p className="mt-2 text-sm text-zinc-500">
            היכנסו לסביבת העבודה התפעולית
          </p>
        </div>

        {configWarning ? (
          <div className="of-card of-card-p6 of-badge-danger mb-5 rounded-2xl text-sm">
            {configWarning}
          </div>
        ) : null}

        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="mb-2 block font-medium">
              אימייל
            </label>

            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="of-input of-focus-ring"
            />
          </div>

          <div>
            <label className="mb-2 block font-medium">
              סיסמה
            </label>

            <div className="relative">
              <input
                type={passwordRevealed ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="of-input of-focus-ring pe-12"
                autoComplete="current-password"
              />

              <button
                type="button"
                tabIndex={-1}
                aria-label="הצג סיסמה בזמן לחיצה"
                className="
                  absolute
                  end-3
                  top-1/2
                  -translate-y-1/2
                  rounded-lg
                  p-1.5
                  text-zinc-400
                  transition-colors
                  select-none
                  touch-none
                  hover:text-zinc-600
                  active:text-brand
                  dark:hover:text-zinc-300
                  dark:active:text-brand-light
                "
                onPointerDown={(e) => {
                  e.preventDefault();
                  setPasswordRevealed(true);
                }}
                onPointerUp={() => setPasswordRevealed(false)}
                onPointerLeave={() => setPasswordRevealed(false)}
                onPointerCancel={() => setPasswordRevealed(false)}
              >
                <Eye
                  className="h-5 w-5"
                  aria-hidden
                />
              </button>
            </div>
          </div>

          {error || authBootstrapError ? (
            <div className="of-card of-card-p6 of-badge-danger rounded-2xl text-sm">
              {error || authBootstrapError}
            </div>
          ) : null}

          <Button
            type="submit"
            variant="accent"
            size="lg"
            disabled={loading || awaitingRedirect}
            className="w-full"
          >
            {loading || awaitingRedirect ? "מתחבר..." : "התחבר"}
          </Button>
        </form>

        <p className="mt-8 text-center text-sm text-zinc-500">
          <Link
            href="/"
            className="font-medium text-brand hover:underline dark:text-brand-light"
          >
            חזרה לדף הבית
          </Link>
        </p>
      </div>
    </main>
  );
}
