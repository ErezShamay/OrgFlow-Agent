"use client";

import {
  useRouter,
} from "next/navigation";

import {
  useAuth,
} from "@/contexts/AuthContext";

export default function UserMenu() {

  const {
    user,
    profile,
    signOut,
  } = useAuth();

  const router =
    useRouter();

  async function handleLogout() {

    await signOut();

    router.push(
      "/auth/login"
    );
  }

  if (!user) {
    return null;
  }

  return (

    <div
      className="
        flex
        items-center
        gap-4
      "
    >

      <div
        className="
          text-right
        "
      >

        <p
          className="
            font-semibold
          "
        >
          {
            profile?.full_name
            || user.email
          }
        </p>

        <div
          className="
            flex
            items-center
            gap-2
            justify-end
            mt-1
          "
        >

          <p
            className="
              text-sm
              text-zinc-500
            "
          >
            {
              profile?.email
            }
          </p>

          <span
            className={`
              text-xs
              px-2
              py-1
              rounded-full
              font-semibold

              ${
                profile?.role
                === "ADMIN"

                  ? `
                    bg-red-100
                    text-red-700
                  `

                  : profile?.role
                  === "MANAGER"

                  ? `
                    bg-blue-100
                    text-blue-700
                  `

                  : `
                    bg-zinc-100
                    text-zinc-700
                  `
              }
            `}
          >
            {
              profile?.role
            }
          </span>

        </div>

      </div>

      <button
        onClick={handleLogout}
        className="
          px-4
          py-2
          rounded-xl
          bg-red-600
          text-white
          hover:bg-red-700
          transition
        "
      >
        התנתק
      </button>

    </div>
  );
}