"use client";

import { useI18n } from "@/providers/I18nProvider";

export default function FilterBar({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  const { t } = useI18n();

  return (
    <label className="block">
      <span className="of-sr-only">{t("common.filter")}</span>
      <input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder ?? t("common.filter")}
        className="
          of-focus-ring
          w-full
          rounded-2xl
          border
          border-zinc-200
          bg-white
          px-4
          py-3
          text-sm
          dark:border-zinc-800
          dark:bg-zinc-900
        "
        aria-label={t("common.filter")}
      />
    </label>
  );
}
