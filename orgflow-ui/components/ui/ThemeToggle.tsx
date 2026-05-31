"use client";

import Button from "@/components/ui/Button";
import { useTheme } from "@/providers/ThemeProvider";

export default function ThemeToggle() {
  const { resolvedTheme, toggleTheme } = useTheme();

  return (
    <Button
      variant="secondary"
      size="sm"
      onClick={toggleTheme}
      aria-label="Toggle color theme"
    >
      {resolvedTheme === "dark" ? "Light mode" : "Dark mode"}
    </Button>
  );
}
