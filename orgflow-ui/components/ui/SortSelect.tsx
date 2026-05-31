"use client";

import type { SortOption } from "@/lib/ui/sorting";
import { getAriaSort } from "@/lib/ui/accessibility";
import { useI18n } from "@/providers/I18nProvider";

export default function SortSelect<K extends string>({
  options,
  sortKey,
  direction,
  onChange,
}: {
  options: SortOption<K>[];
  sortKey: K;
  direction: "asc" | "desc";
  onChange: (key: K) => void;
}) {
  const { t } = useI18n();

  return (
    <label className="block">
      <span className="mb-2 block text-sm font-medium text-zinc-600 dark:text-zinc-400">
        {t("common.sort")}
      </span>
      <select
        value={sortKey}
        onChange={(event) => onChange(event.target.value as K)}
        aria-sort={getAriaSort(direction)}
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
      >
        {options.map((option) => (
          <option key={option.key} value={option.key}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
