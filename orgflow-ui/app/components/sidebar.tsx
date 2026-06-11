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
} from "@/hooks/useEffectiveRole";
import { useFieldReportModule } from "@/hooks/useFieldReportModule";
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
  isQCPrimaryNavActive,
  isQCProjectNavActive,
} from "@/lib/qc-navigation";

export default function Sidebar() {
  const pathname = usePathname();
  const params = useParams();
  const effectiveRole = useEffectiveRole();
  const isAdminUser = useIsAdmin();
  const { isEnabled: fieldReportsEnabled } = useFieldReportModule();
  const projectId =
    typeof params?.id === "string"
      ? params.id
      : null;

  const contractorView = isContractorRole(effectiveRole);
  const systemLinks = contractorView
    ? [SETTINGS_ROUTE]
    : getSystemNavLinks(isAdminUser);

  const primaryLinks = getQCPrimaryNavLinks({
    role: effectiveRole,
    fieldReportsEnabled: fieldReportsEnabled,
  });

  const projectPrimaryLinks = projectId
    ? getQCProjectPrimaryNavLinks(projectId, effectiveRole).filter((link) => {
        if (!fieldReportsEnabled && link.href.endsWith("/field-reports")) {
          return false;
        }

        return true;
      })
    : [];

  const projectSecondaryLinks = projectId
    ? getQCProjectSecondaryNavLinks(projectId, effectiveRole)
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

        <div>
          <p className="of-nav-section-label">
            מערכת
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
