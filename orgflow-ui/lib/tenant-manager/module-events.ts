export const TENANT_MANAGER_MODULE_CHANGED_EVENT =
  "tenant-manager-module-changed";

export function dispatchTenantManagerModuleChanged(
  organizationId?: string
) {
  if (typeof window === "undefined") {
    return;
  }

  window.dispatchEvent(
    new CustomEvent(TENANT_MANAGER_MODULE_CHANGED_EVENT, {
      detail: { organizationId },
    })
  );
}
