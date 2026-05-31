"use client";

import { useMemo, useState } from "react";

import {
  sortItems,
  toggleSortDirection,
  type SortDirection,
  type SortOption,
} from "@/lib/ui/sorting";

export function useSorting<T, K extends string>(
  items: T[],
  options: SortOption<K>[],
  getValue: (item: T, key: K) => string | number,
  initialKey?: K,
  initialDirection: SortDirection = "asc"
) {
  const [sortKey, setSortKey] = useState<K>(
    initialKey ?? options[0]?.key
  );
  const [direction, setDirection] =
    useState<SortDirection>(initialDirection);

  const sortedItems = useMemo(() => {
    if (!sortKey) {
      return items;
    }

    return sortItems(
      items,
      (item) => getValue(item, sortKey),
      direction
    );
  }, [items, sortKey, direction, getValue]);

  const setSort = (key: K) => {
    if (key === sortKey) {
      setDirection(toggleSortDirection(direction));
      return;
    }

    setSortKey(key);
    setDirection("asc");
  };

  return {
    sortKey,
    direction,
    sortedItems,
    setSort,
    options,
  };
}
