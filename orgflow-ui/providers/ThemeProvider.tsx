"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type ThemeMode = "light" | "dark" | "system";

type ThemeContextValue = {
  theme: ThemeMode;
  resolvedTheme: "light" | "dark";
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(
  null
);

const STORAGE_KEY = "orgflow-theme";

function resolveTheme(theme: ThemeMode): "light" | "dark" {
  if (theme === "system" && typeof window !== "undefined") {
    return window.matchMedia("(prefers-color-scheme: dark)")
      .matches
      ? "dark"
      : "light";
  }

  return theme === "dark" ? "dark" : "light";
}

export function ThemeProvider({
  children,
  defaultTheme = "system",
}: {
  children: ReactNode;
  defaultTheme?: ThemeMode;
}) {
  const [theme, setThemeState] = useState<ThemeMode>(
    defaultTheme
  );
  const [resolvedTheme, setResolvedTheme] = useState<
    "light" | "dark"
  >("light");

  useEffect(() => {
    const stored = window.localStorage.getItem(
      STORAGE_KEY
    ) as ThemeMode | null;

    if (stored) {
      setThemeState(stored);
    }
  }, []);

  useEffect(() => {
    const resolved = resolveTheme(theme);
    setResolvedTheme(resolved);
    document.documentElement.classList.toggle(
      "dark",
      resolved === "dark"
    );
    window.localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  useEffect(() => {
    if (theme !== "system") {
      return;
    }

    const media = window.matchMedia(
      "(prefers-color-scheme: dark)"
    );
    const listener = () =>
      setResolvedTheme(resolveTheme("system"));

    media.addEventListener("change", listener);
    return () => media.removeEventListener("change", listener);
  }, [theme]);

  const setTheme = useCallback((next: ThemeMode) => {
    setThemeState(next);
  }, []);

  const toggleTheme = useCallback(() => {
    setThemeState((current) => {
      const resolved = resolveTheme(current);
      return resolved === "dark" ? "light" : "dark";
    });
  }, []);

  const value = useMemo(
    () => ({
      theme,
      resolvedTheme,
      setTheme,
      toggleTheme,
    }),
    [theme, resolvedTheme, setTheme, toggleTheme]
  );

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);

  if (!context) {
    throw new Error(
      "useTheme must be used within ThemeProvider"
    );
  }

  return context;
}
