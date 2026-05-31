export function getAriaSort(
  direction: "asc" | "desc" | null
): "ascending" | "descending" | "none" {
  if (direction === "asc") {
    return "ascending";
  }

  if (direction === "desc") {
    return "descending";
  }

  return "none";
}

export function buildListboxId(id: string): string {
  return `${id}-listbox`;
}

export function announceLiveRegion(
  message: string,
  priority: "polite" | "assertive" = "polite"
): void {
  if (typeof document === "undefined") {
    return;
  }

  const region = document.createElement("div");
  region.setAttribute("role", "status");
  region.setAttribute("aria-live", priority);
  region.setAttribute("aria-atomic", "true");
  region.className = "of-sr-only";
  region.textContent = message;

  document.body.appendChild(region);

  window.setTimeout(() => {
    document.body.removeChild(region);
  }, 1000);
}
