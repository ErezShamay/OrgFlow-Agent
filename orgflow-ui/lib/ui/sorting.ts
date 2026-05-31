export type SortDirection = "asc" | "desc";

export type SortOption<T extends string = string> = {
  key: T;
  label: string;
};

export function sortItems<T>(
  items: T[],
  getValue: (item: T) => string | number,
  direction: SortDirection = "asc"
): T[] {
  const sorted = [...items].sort((left, right) => {
    const leftValue = getValue(left);
    const rightValue = getValue(right);

    if (typeof leftValue === "number" && typeof rightValue === "number") {
      return leftValue - rightValue;
    }

    return String(leftValue).localeCompare(
      String(rightValue),
      undefined,
      { numeric: true, sensitivity: "base" }
    );
  });

  return direction === "desc" ? sorted.reverse() : sorted;
}

export function toggleSortDirection(
  direction: SortDirection
): SortDirection {
  return direction === "asc" ? "desc" : "asc";
}
