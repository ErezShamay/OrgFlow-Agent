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
        className="of-input of-focus-ring px-4 py-3 text-sm"
        aria-label={t("common.filter")}
      />
    </label>
  );
}
