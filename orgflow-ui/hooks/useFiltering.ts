"use client";

import { useMemo, useState } from "react";

import {
  buildSearchFilter,
  filterItems,
  type FilterRule,
} from "@/lib/ui/filtering";

export function useFiltering<T, F extends string>(
  items: T[],
  getFieldValue: (item: T, field: F) => string | number,
  searchField?: F
) {
  const [rules, setRules] = useState<FilterRule<F>[]>([]);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredItems = useMemo(() => {
    const searchRules = searchField
      ? buildSearchFilter(searchField, searchQuery)
      : [];

    return filterItems(
      items,
      [...rules, ...searchRules],
      getFieldValue
    );
  }, [items, rules, searchQuery, searchField, getFieldValue]);

  const addRule = (rule: FilterRule<F>) => {
    setRules((current) => [...current, rule]);
  };

  const clearRules = () => {
    setRules([]);
    setSearchQuery("");
  };

  return {
    filteredItems,
    rules,
    searchQuery,
    setSearchQuery,
    addRule,
    clearRules,
    setRules,
  };
}
