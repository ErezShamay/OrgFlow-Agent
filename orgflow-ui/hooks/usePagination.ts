"use client";

import { useMemo, useState } from "react";

import {
  getPageNumbers,
  paginateItems,
  type PaginationResult,
} from "@/lib/ui/pagination";

export function usePagination<T>(
  items: T[],
  initialPageSize = 10
) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);

  const result: PaginationResult<T> = useMemo(
    () => paginateItems(items, page, pageSize),
    [items, page, pageSize]
  );

  const pageNumbers = useMemo(
    () =>
      getPageNumbers(
        result.state.page,
        result.totalPages
      ),
    [result.state.page, result.totalPages]
  );

  return {
    ...result,
    pageNumbers,
    setPage,
    setPageSize,
    goToNextPage: () => {
      if (result.hasNextPage) {
        setPage((current) => current + 1);
      }
    },
    goToPreviousPage: () => {
      if (result.hasPreviousPage) {
        setPage((current) => current - 1);
      }
    },
  };
}
