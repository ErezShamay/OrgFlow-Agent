"use client";

import {
  useParams,
  usePathname,
} from "next/navigation";

import BrandLogo from "@/components/ui/BrandLogo";
import NavLinkItem from "@/components/ui/NavLinkItem";
import {
  useEffectiveRole,
  useIsAdmin,
  useIsPlatformAdmin,
} from "@/hooks/useEffectiveRole";
import { useFieldReportModule } from "@/hooks/useFieldReportModule";
import { useTenantManagerModule } from "@/hooks/useTenantManagerModule";
import { isContractorRole } from "@/lib/auth/contractor-access";
import {
  getSystemNavLinks,
  isNavLinkActive,
  SETTINGS_ROUTE,
} from "@/lib/navigation";
import {
  getQCPrimaryNavLinks,
  getQCProjectNavLinks,
  getQCProjectPrimaryNavLinks,
  getQCProjectSecondaryNavLinks,
  getToolsNavLinks,
  isQCPrimaryNavActive,
  isQCProjectNavActive,
  isToolsNavActive,
  TOOLS_NAV_LABEL,
} from "@/lib/qc-navigation";

export default function Sidebar() {
  const pathname = usePathname();
  const params = useParams();
  const effectiveRole = useEffectiveRole();
  const isAdminUser = useIsAdmin();
  const isPlatformAdminUser = useIsPlatformAdmin();
  const { isEnabled: fieldReportsEnabled } = useFieldReportModule();
  const { isEnabled: tenantManagerEnabled } = useTenantManagerModule();
  const projectId =
    typeof params?.id === "string"
      ? params.id
      : null;

  const contractorView = isContractorRole(effectiveRole);
  const showClientNavigation = !contractorView && !isPlatformAdminUser;
  const systemLinks = contractorView
    ? [SETTINGS_ROUTE]
    : getSystemNavLinks(isAdminUser, {
        platformAdmin: isPlatformAdminUser,
      });

  const primaryLinks = showClientNavigation
    ? getQCPrimaryNavLinks({
        role: effectiveRole,
        fieldReportsEnabled: fieldReportsEnabled,
      })
    : [];

  const projectPrimaryLinks =
    showClientNavigation && projectId
      ? getQCProjectPrimaryNavLinks(projectId, effectiveRole)
      : [];

  const projectSecondaryLinks =
    showClientNavigation && projectId
      ? getQCProjectSecondaryNavLinks(projectId, effectiveRole)
      : [];

  const toolsLinks =
    showClientNavigation
      ? getToolsNavLinks({ tenantManagerEnabled })
      : [];

  return (
    <aside
      className="
        of-glass-sidebar
        w-full
        border-b
        p-4
        lg:w-72
        lg:min-h-screen
        lg:border-b-0
        lg:border-l
        lg:p-6
      "
    >
      <div className="mb-10">
        <BrandLogo size="lg" />
      </div>

      <nav className="space-y-6">
        {primaryLinks.length > 0 ? (
          <div>
            <p className="of-nav-section-label">
              ניווט ראשי
            </p>

            <div className="space-y-1">
              {primaryLinks.map((link) => (
                <NavLinkItem
                  key={link.href}
                  href={link.href}
                  label={link.label}
                  isActive={isQCPrimaryNavActive(pathname, link.href)}
                />
              ))}
            </div>
          </div>
        ) : null}

        {projectPrimaryLinks.length > 0 ? (
          <div>
            <p className="of-nav-section-label">
              פרויקט נוכחי
            </p>

            <div className="space-y-1">
              {projectPrimaryLinks.map((link) => (
                <NavLinkItem
                  key={link.href}
                  href={link.href}
                  label={link.label}
                  isActive={isQCProjectNavActive(pathname, link.href)}
                />
              ))}
            </div>
          </div>
        ) : null}

        {projectSecondaryLinks.length > 0 ? (
          <div>
            <p className="of-nav-section-label">
              משני בפרויקט
            </p>

            <div className="space-y-1">
              {projectSecondaryLinks.map((link) => (
                <NavLinkItem
                  key={link.href}
                  href={link.href}
                  label={link.label}
                  isActive={isQCProjectNavActive(pathname, link.href)}
                />
              ))}
            </div>
          </div>
        ) : null}

        {toolsLinks.length > 0 ? (
          <div>
            <p className="of-nav-section-label">
              {TOOLS_NAV_LABEL}
            </p>

            <div className="space-y-1">
              {toolsLinks.map((link) => (
                <NavLinkItem
                  key={link.href}
                  href={link.href}
                  label={link.label}
                  isActive={isToolsNavActive(pathname, link.href)}
                />
              ))}
            </div>
          </div>
        ) : null}

        <div>
          <p className="of-nav-section-label">
            {isPlatformAdminUser
              ? "ניהול פלטפורמה"
              : "מערכת"}
          </p>

          <div className="space-y-1">
            {systemLinks.map((link) => (
              <NavLinkItem
                key={link.href}
                href={link.href}
                label={link.label}
                isActive={isNavLinkActive(pathname, link.href)}
              />
            ))}
          </div>
        </div>
      </nav>
    </aside>
  );
}
