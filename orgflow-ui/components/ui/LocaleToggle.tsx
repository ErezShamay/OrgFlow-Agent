"use client";

import Button from "@/components/ui/Button";
import { useI18n } from "@/providers/I18nProvider";

export default function LocaleToggle() {
  const { locale, setLocale } = useI18n();

  return (
    <Button
      variant="secondary"
      size="sm"
      onClick={() => setLocale(locale === "he" ? "en" : "he")}
      aria-label="Toggle language"
    >
      {locale === "he" ? "English" : "עברית"}
    </Button>
  );
}
