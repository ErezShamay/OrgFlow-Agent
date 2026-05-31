"use client";

import { useCallback, useEffect, useState, startTransition } from "react";

import { useRouter } from "next/navigation";

import { Bell } from "lucide-react";

import { useAuth } from "@/contexts/AuthContext";
import { useRealtime } from "@/hooks/useRealtime";
import { apiFetch } from "@/lib/api/client";

type Notification = {

  id: string;

  title: string;

  message: string;

  notification_type: string;

  is_read: boolean;

  created_at: string;
};

export default function UserMenu() {

  const {
    user,
    profile,
    signOut,
  } = useAuth();

  const router =
    useRouter();

  const [
    notifications,
    setNotifications
  ] = useState<
    Notification[]
  >([]);

  const [
    showNotifications,
    setShowNotifications
  ] = useState(false);

  const loadNotifications = useCallback(async () => {
    try {
      const response =
        await apiFetch(
          `/profiles/${profile?.id}/notifications`
        );

      if (!response.ok) {
        throw new Error(
          "Failed loading notifications"
        );
      }

      const data =
        await response.json();

      setNotifications(data);

    } catch (error) {

      console.error(error);
    }
  }, [profile]);

  useEffect(() => {

    if (
      profile?.id
    ) {

      startTransition(() => {
        void loadNotifications();
      });
    }

  }, [profile?.id, loadNotifications]);

  useRealtime({
    channelName: `notifications-live-${profile?.id ?? "guest"}`,
    table: "notifications",
    enabled: Boolean(profile?.id),
    onChange: () => {
      void loadNotifications();
    },
  });

  async function markAsRead(
    notificationId: string
  ) {

    try {

      await apiFetch(
        `/notifications/${notificationId}/read`,
        {
          method: "PATCH",
        }
      );

      setNotifications(
        notifications.map(
          (notification) =>

            notification.id
            === notificationId

              ? {
                  ...notification,
                  is_read: true,
                }

              : notification
        )
      );

    } catch (error) {

      console.error(error);
    }
  }

  async function handleLogout() {
    await signOut();
    router.push("/");
  }

  if (!user) {
    return null;
  }

  const unreadCount =
    notifications.filter(
      n => !n.is_read
    ).length;

  return (

    <div
      className="
        flex
        items-center
        gap-4
      "
    >

      {/* NOTIFICATIONS */}

      <div className="relative">

        <button
          onClick={() =>
            setShowNotifications(
              !showNotifications
            )
          }
          className="
            relative
            p-3
            rounded-2xl
            border
            border-zinc-200
            dark:border-zinc-700
            hover:bg-zinc-100
            dark:hover:bg-zinc-800
            transition
          "
        >

          <Bell size={20} />

          {
            unreadCount > 0
            && (

              <span
                className="
                  absolute
                  -top-2
                  -left-2
                  min-w-[24px]
                  h-6
                  px-1
                  rounded-full
                  bg-red-600
                  text-white
                  text-xs
                  flex
                  items-center
                  justify-center
                  font-bold
                "
              >
                {unreadCount}
              </span>

            )
          }

        </button>

        {
          showNotifications
          && (

            <div
              className="
                absolute
                left-0
                top-14
                w-[420px]
                max-h-[500px]
                overflow-auto
                bg-white
                dark:bg-zinc-900
                border
                border-zinc-200
                dark:border-zinc-800
                rounded-3xl
                shadow-2xl
                z-50
              "
            >

              <div
                className="
                  p-5
                  border-b
                  border-zinc-200
                  dark:border-zinc-800
                "
              >

                <h3
                  className="
                    text-xl
                    font-bold
                  "
                >
                  Notifications
                </h3>

              </div>

              <div className="p-3 space-y-3">

                {
                  notifications.length === 0
                  && (

                    <div
                      className="
                        p-6
                        text-center
                        text-zinc-500
                      "
                    >
                      אין התראות
                    </div>

                  )
                }

                {
                  notifications.map(
                    (notification) => (

                      <button
                        key={notification.id}
                        onClick={() =>
                          markAsRead(
                            notification.id
                          )
                        }
                        className={`
                          w-full
                          text-right
                          p-5
                          rounded-2xl
                          border
                          transition

                          ${
                            notification.is_read

                              ? `
                                border-zinc-200
                                dark:border-zinc-800
                                opacity-70
                              `

                              : `
                                border-blue-300
                                bg-blue-50
                                dark:bg-blue-950/30
                              `
                          }
                        `}
                      >

                        <div
                          className="
                            flex
                            justify-between
                            items-start
                            gap-4
                          "
                        >

                          <div>

                            <h4
                              className="
                                font-bold
                              "
                            >
                              {
                                notification.title
                              }
                            </h4>

                            <p
                              className="
                                mt-2
                                text-sm
                                text-zinc-600
                                dark:text-zinc-400
                                leading-6
                              "
                            >
                              {
                                notification.message
                              }
                            </p>

                          </div>

                          {
                            !notification.is_read
                            && (

                              <span
                                className="
                                  w-3
                                  h-3
                                  rounded-full
                                  bg-blue-600
                                  mt-2
                                "
                              />

                            )
                          }

                        </div>

                        <p
                          className="
                            mt-4
                            text-xs
                            text-zinc-500
                          "
                        >
                          {
                            new Date(
                              notification.created_at
                            ).toLocaleString(
                              "he-IL"
                            )
                          }
                        </p>

                      </button>

                    )
                  )
                }

              </div>

            </div>

          )
        }

      </div>

      {/* USER */}

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

      {/* LOGOUT */}

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