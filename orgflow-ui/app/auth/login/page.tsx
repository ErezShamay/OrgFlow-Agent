"use client";

import {
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";

import { supabase } from "@/lib/supabase";

export default function LoginPage() {

  const router =
    useRouter();

  const [
    email,
    setEmail
  ] = useState("");

  const [
    password,
    setPassword
  ] = useState("");

  const [
    loading,
    setLoading
  ] = useState(false);

  const [
    error,
    setError
  ] = useState("");

  async function handleLogin(
    e: React.FormEvent
  ) {

    e.preventDefault();

    try {

      setLoading(true);

      setError("");

      const {
        error,
      } = await supabase.auth.signInWithPassword({

        email,

        password,
      });

      if (error) {

        throw error;
      }

      router.push(
        "/portfolio"
      );

    } catch (err: any) {

      setError(
        err.message
        || "Login failed"
      );

    } finally {

      setLoading(false);
    }
  }

  return (

    <main
      className="
        min-h-screen
        flex
        items-center
        justify-center
        bg-zinc-100
        dark:bg-zinc-950
        p-6
      "
    >

      <div
        className="
          w-full
          max-w-md
          bg-white
          dark:bg-zinc-900
          border
          border-zinc-200
          dark:border-zinc-800
          rounded-3xl
          p-10
          shadow-sm
        "
      >

        <div className="mb-8">

          <p
            className="
              text-zinc-500
              mb-2
            "
          >
            Supervisor AI
          </p>

          <h1
            className="
              text-4xl
              font-black
            "
          >
            התחברות
          </h1>

        </div>

        <form
          onSubmit={handleLogin}
          className="space-y-5"
        >

          <div>

            <label
              className="
                block
                mb-2
                font-medium
              "
            >
              אימייל
            </label>

            <input
              type="email"
              value={email}
              onChange={(e) =>
                setEmail(
                  e.target.value
                )
              }
              required
              className="
                w-full
                rounded-2xl
                border
                border-zinc-200
                dark:border-zinc-700
                bg-transparent
                p-4
                outline-none
              "
            />

          </div>

          <div>

            <label
              className="
                block
                mb-2
                font-medium
              "
            >
              סיסמה
            </label>

            <input
              type="password"
              value={password}
              onChange={(e) =>
                setPassword(
                  e.target.value
                )
              }
              required
              className="
                w-full
                rounded-2xl
                border
                border-zinc-200
                dark:border-zinc-700
                bg-transparent
                p-4
                outline-none
              "
            />

          </div>

          {error && (

            <div
              className="
                p-4
                rounded-2xl
                bg-red-100
                text-red-700
                text-sm
              "
            >
              {error}
            </div>

          )}

          <button
            type="submit"
            disabled={loading}
            className="
              w-full
              py-4
              rounded-2xl
              bg-blue-600
              text-white
              font-bold
              hover:bg-blue-700
              transition
            "
          >

            {
              loading

                ? "מתחבר..."

                : "התחבר"
            }

          </button>

        </form>

      </div>

    </main>
  );
}