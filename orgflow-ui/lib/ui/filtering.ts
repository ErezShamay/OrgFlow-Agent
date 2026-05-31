export type FilterOperator =
  | "equals"
  | "contains"
  | "startsWith"
  | "gt"
  | "lt";

export type FilterRule<T extends string = string> = {
  field: T;
  operator: FilterOperator;
  value: string | number;
};

export function matchesFilterRule(
  value: string | number,
  rule: FilterRule
): boolean {
  const normalizedValue = String(value).toLowerCase();
  const normalizedRule = String(rule.value).toLowerCase();

  switch (rule.operator) {
    case "equals":
      return normalizedValue === normalizedRule;
    case "contains":
      return normalizedValue.includes(normalizedRule);
    case "startsWith":
      return normalizedValue.startsWith(normalizedRule);
    case "gt":
      return Number(value) > Number(rule.value);
    case "lt":
      return Number(value) < Number(rule.value);
    default:
      return true;
  }
}

export function filterItems<T, F extends string>(
  items: T[],
  rules: FilterRule<F>[],
  getFieldValue: (item: T, field: F) => string | number
): T[] {
  if (rules.length === 0) {
    return items;
  }

  return items.filter((item) =>
    rules.every((rule) =>
      matchesFilterRule(
        getFieldValue(item, rule.field),
        rule
      )
    )
  );
}

export function buildSearchFilter<T extends string>(
  field: T,
  query: string
): FilterRule<T>[] {
  const trimmed = query.trim();

  if (!trimmed) {
    return [];
  }

  return [
    {
      field,
      operator: "contains",
      value: trimmed,
    },
  ];
}
