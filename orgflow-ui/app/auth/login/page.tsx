"use client";

import Link from "next/link";

import {
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";

import BrandLogo from "@/components/ui/BrandLogo";
import Button from "@/components/ui/Button";
import { supabase } from "@/lib/supabase";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();

    try {
      setLoading(true);
      setError("");

      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        throw error;
      }

      router.push("/");
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Login failed"
      );
    } finally {
      setLoading(false);
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
          <p className="mb-2 text-sm font-medium text-blue-600 dark:text-blue-400">
            ברוכים השבים
          </p>
          <h1 className="text-3xl font-black tracking-tight">
            התחברות
          </h1>
          <p className="mt-2 text-sm text-zinc-500">
            היכנסו לסביבת העבודה התפעולית
          </p>
        </div>

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

            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="of-input of-focus-ring"
            />
          </div>

          {error ? (
            <div className="of-card of-card-p6 of-badge-danger rounded-2xl text-sm">
              {error}
            </div>
          ) : null}

          <Button
            type="submit"
            variant="accent"
            size="lg"
            disabled={loading}
            className="w-full"
          >
            {loading ? "מתחבר..." : "התחבר"}
          </Button>
        </form>

        <p className="mt-8 text-center text-sm text-zinc-500">
          <Link
            href="/"
            className="font-medium text-blue-600 hover:underline dark:text-blue-400"
          >
            חזרה לדף הבית
          </Link>
        </p>
      </div>
    </main>
  );
}
