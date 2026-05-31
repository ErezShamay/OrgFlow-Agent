export type PaginationState = {
  page: number;
  pageSize: number;
  totalItems: number;
};

export type PaginationResult<T> = {
  items: T[];
  state: PaginationState;
  totalPages: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
};

export function paginateItems<T>(
  items: T[],
  page: number,
  pageSize: number
): PaginationResult<T> {
  const safePageSize = Math.max(1, pageSize);
  const totalItems = items.length;
  const totalPages = Math.max(
    1,
    Math.ceil(totalItems / safePageSize)
  );
  const safePage = Math.min(
    Math.max(1, page),
    totalPages
  );
  const start = (safePage - 1) * safePageSize;
  const end = start + safePageSize;

  return {
    items: items.slice(start, end),
    state: {
      page: safePage,
      pageSize: safePageSize,
      totalItems,
    },
    totalPages,
    hasNextPage: safePage < totalPages,
    hasPreviousPage: safePage > 1,
  };
}

export function getPageNumbers(
  currentPage: number,
  totalPages: number,
  maxVisible = 5
): number[] {
  if (totalPages <= maxVisible) {
    return Array.from(
      { length: totalPages },
      (_, index) => index + 1
    );
  }

  const half = Math.floor(maxVisible / 2);
  let start = Math.max(1, currentPage - half);
  const end = Math.min(
    totalPages,
    start + maxVisible - 1
  );

  start = Math.max(1, end - maxVisible + 1);

  return Array.from(
    { length: end - start + 1 },
    (_, index) => start + index
  );
}
