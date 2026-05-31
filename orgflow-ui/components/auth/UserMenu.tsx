"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  startTransition,
} from "react";

import { useRouter } from "next/navigation";

import { Bell, ChevronDown, LogOut } from "lucide-react";

import { useAuth } from "@/contexts/AuthContext";
import { useRealtime } from "@/hooks/useRealtime";
import { apiFetch } from "@/lib/api/client";
import { normalizeRole } from "@/lib/auth/role";
import { getRoleLabel, getRoleBadgeClass } from "@/lib/auth/roleLabels";

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
    sessionRole,
    signOut,
  } = useAuth();

  const effectiveRole = normalizeRole(
    profile?.role || sessionRole
  );

  const router = useRouter();
  const notificationsRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const loadNotifications = useCallback(async () => {
    try {
      const response = await apiFetch(
        `/profiles/${profile?.id}/notifications`
      );

      if (!response.ok) {
        throw new Error("Failed loading notifications");
      }

      const data = await response.json();
      setNotifications(data);
    } catch (error) {
      console.error(error);
    }
  }, [profile]);

  useEffect(() => {
    if (profile?.id) {
      startTransition(() => {
        void loadNotifications();
      });
    }
  }, [profile?.id, loadNotifications]);

  useEffect(() => {
    if (!showNotifications && !showUserMenu) {
      return;
    }

    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Node;

      if (
        showNotifications
        && notificationsRef.current
        && !notificationsRef.current.contains(target)
      ) {
        setShowNotifications(false);
      }

      if (
        showUserMenu
        && userMenuRef.current
        && !userMenuRef.current.contains(target)
      ) {
        setShowUserMenu(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showNotifications, showUserMenu]);

  useRealtime({
    channelName: `notifications-live-${profile?.id ?? "guest"}`,
    table: "notifications",
    enabled: Boolean(profile?.id),
    onChange: () => {
      void loadNotifications();
    },
  });

  async function markAsRead(notificationId: string) {
    try {
      await apiFetch(
        `/notifications/${notificationId}/read`,
        { method: "PATCH" }
      );

      setNotifications(
        notifications.map((notification) =>
          notification.id === notificationId
            ? { ...notification, is_read: true }
            : notification
        )
      );
    } catch (error) {
      console.error(error);
    }
  }

  async function handleLogout() {
    setShowUserMenu(false);
    await signOut();
    router.push("/");
  }

  if (!user) {
    return null;
  }

  const unreadCount = notifications.filter((n) => !n.is_read).length;
  const displayName = profile?.full_name || user.email;

  return (
    <div className="flex items-center gap-4">
      <div className="relative" ref={notificationsRef}>
        <button
          type="button"
          onClick={() => {
            setShowNotifications((current) => !current);
            setShowUserMenu(false);
          }}
          className="
            of-focus-ring
            relative
            rounded-2xl
            border
            border-zinc-200/80
            bg-white/90
            p-3
            transition
            hover:bg-zinc-50
            dark:border-zinc-700/80
            dark:bg-zinc-900/85
            dark:hover:bg-zinc-800
          "
          aria-expanded={showNotifications}
          aria-label="התראות"
        >
          <Bell size={20} />

          {unreadCount > 0 ? (
            <span
              className="
                absolute
                -top-2
                -left-2
                flex
                h-6
                min-w-[24px]
                items-center
                justify-center
                rounded-full
                bg-red-600
                px-1
                text-xs
                font-bold
                text-white
              "
            >
              {unreadCount}
            </span>
          ) : null}
        </button>

        {showNotifications ? (
          <div
            className="
              of-card
              absolute
              left-0
              top-14
              z-50
              max-h-[500px]
              w-[420px]
              overflow-auto
              p-0
              shadow-2xl
            "
          >
            <div
              className="
                border-b
                border-zinc-200
                p-5
                dark:border-zinc-800
              "
            >
              <h3 className="text-xl font-bold">Notifications</h3>
            </div>

            <div className="space-y-3 p-3">
              {notifications.length === 0 ? (
                <div className="p-6 text-center text-zinc-500">
                  אין התראות
                </div>
              ) : null}

              {notifications.map((notification) => (
                <button
                  key={notification.id}
                  type="button"
                  onClick={() => markAsRead(notification.id)}
                  className={`
                    w-full
                    rounded-2xl
                    border
                    p-5
                    text-right
                    transition
                    ${
                      notification.is_read
                        ? `
                          border-zinc-200
                          opacity-70
                          dark:border-zinc-800
                        `
                        : `
                          border-blue-300
                          bg-blue-50
                          dark:bg-blue-950/30
                        `
                    }
                  `}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h4 className="font-bold">{notification.title}</h4>
                      <p
                        className="
                          mt-2
                          text-sm
                          leading-6
                          text-zinc-600
                          dark:text-zinc-400
                        "
                      >
                        {notification.message}
                      </p>
                    </div>

                    {!notification.is_read ? (
                      <span
                        className="
                          mt-2
                          h-3
                          w-3
                          rounded-full
                          bg-blue-600
                        "
                      />
                    ) : null}
                  </div>

                  <p className="mt-4 text-xs text-zinc-500">
                    {new Date(notification.created_at).toLocaleString("he-IL")}
                  </p>
                </button>
              ))}
            </div>
          </div>
        ) : null}
      </div>

      <div className="relative" ref={userMenuRef}>
        <button
          type="button"
          onClick={() => {
            setShowUserMenu((current) => !current);
            setShowNotifications(false);
          }}
          className="
            of-focus-ring
            flex
            items-center
            gap-2
            rounded-2xl
            border
            border-zinc-200/80
            bg-white/90
            px-3
            py-2
            text-right
            transition
            hover:bg-zinc-50
            dark:border-zinc-700/80
            dark:bg-zinc-900/85
            dark:hover:bg-zinc-800
          "
          aria-expanded={showUserMenu}
          aria-haspopup="menu"
        >
          <div>
            <p className="font-semibold">{displayName}</p>

            <div className="mt-1 flex items-center justify-end gap-2">
              {profile?.email ? (
                <p className="hidden text-sm text-zinc-500 sm:block">
                  {profile.email}
                </p>
              ) : null}

              <span
                className={`
                  rounded-full
                  px-2
                  py-1
                  text-xs
                  font-semibold
                  ${getRoleBadgeClass(effectiveRole)}
                `}
              >
                {getRoleLabel(effectiveRole)}
              </span>
            </div>
          </div>

          <ChevronDown
            size={16}
            className={`
              shrink-0
              text-zinc-500
              transition-transform
              ${showUserMenu ? "rotate-180" : ""}
            `}
          />
        </button>

        {showUserMenu ? (
          <div
            className="
              of-card
              absolute
              left-0
              top-[calc(100%+0.5rem)]
              z-50
              min-w-[220px]
              overflow-hidden
              p-2
              shadow-2xl
            "
            role="menu"
          >
            <div
              className="
                border-b
                border-zinc-200
                px-3
                py-2
                dark:border-zinc-800
              "
            >
              <p className="font-semibold">{displayName}</p>
              {profile?.email ? (
                <p className="mt-1 text-sm text-zinc-500">{profile.email}</p>
              ) : null}
            </div>

            <button
              type="button"
              role="menuitem"
              onClick={() => void handleLogout()}
              className="
                mt-1
                flex
                w-full
                items-center
                gap-2
                rounded-xl
                px-3
                py-2.5
                text-right
                text-sm
                font-medium
                text-red-600
                transition-colors
                hover:bg-red-50
                dark:text-red-400
                dark:hover:bg-red-950/40
              "
            >
              <LogOut size={16} />
              התנתק
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
