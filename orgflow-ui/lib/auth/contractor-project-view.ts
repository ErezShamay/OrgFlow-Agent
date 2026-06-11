import { isContractorRole } from "@/lib/auth/contractor-access";

/** Contractors see project context but not field reports, catalog, or PM artifacts. */
export function isContractorLimitedProjectView(
  role?: string | null
): boolean {
  return isContractorRole(role);
}
