"use client";

import { Monitor, Moon, Sun } from "lucide-react";

import type { ThemeMode } from "@/providers/ThemeProvider";
import { useTheme } from "@/providers/ThemeProvider";

const THEME_OPTIONS: {
  value: ThemeMode;
  label: string;
  description: string;
  icon: typeof Sun;
}[] = [
  {
    value: "light",
    label: "מצב בהיר",
    description: "רקע בהיר וטקסט כהה",
    icon: Sun,
  },
  {
    value: "dark",
    label: "מצב כהה",
    description: "רקע כהה וטקסט בהיר",
    icon: Moon,
  },
  {
    value: "system",
    label: "לפי המערכת",
    description: "מתאים את עצמו להגדרות המכשיר",
    icon: Monitor,
  },
];

export default function ThemeSettings() {
  const { theme, setTheme, resolvedTheme } = useTheme();

  return (
    <section>
      <div className="mb-6">
        <h2 className="text-xl font-bold">
          מראה
        </h2>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          בחרו את ערכת הצבעים של הממשק
          {theme === "system" ? (
            <span>
              {" "}
              (כרגע: {resolvedTheme === "dark" ? "כהה" : "בהיר"})
            </span>
          ) : null}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        {THEME_OPTIONS.map((option) => {
          const isActive = theme === option.value;
          const Icon = option.icon;

          return (
            <button
              key={option.value}
              type="button"
              onClick={() => setTheme(option.value)}
              className={`
                of-focus-ring
                rounded-2xl
                border
                p-4
                text-right
                transition-all
                ${
                  isActive
                    ? `
                      border-blue-500
                      bg-blue-50
                      shadow-md
                      shadow-blue-500/10
                      dark:border-blue-500
                      dark:bg-blue-950/40
                    `
                    : `
                      border-zinc-200/80
                      bg-white/90
                      hover:border-zinc-300
                      hover:bg-zinc-50
                      dark:border-zinc-800
                      dark:bg-zinc-900/85
                      dark:hover:border-zinc-700
                      dark:hover:bg-zinc-800
                    `
                }
              `}
              aria-pressed={isActive}
            >
              <div
                className={`
                  mb-3
                  inline-flex
                  rounded-xl
                  p-2.5
                  ${
                    isActive
                      ? "bg-gradient-to-br from-blue-600 to-violet-600 text-white"
                      : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300"
                  }
                `}
              >
                <Icon className="h-5 w-5" />
              </div>

              <p className="font-semibold">
                {option.label}
              </p>
              <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                {option.description}
              </p>
            </button>
          );
        })}
      </div>
    </section>
  );
}
