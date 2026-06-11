/**
 * QC Spec 0.5 - Freeze list for QC pivot (mirrors app/schemas/qc_freeze.py).
 * See docs/qc-spec/qc-freeze-list.md.
 */

export const QC_FREEZE_CATEGORIES = [
  "FROZEN",
  "DEPRECATED",
  "ADMIN_ONLY",
  "SECONDARY",
] as const;

export type QCFreezeCategory = (typeof QC_FREEZE_CATEGORIES)[number];

export const QC_FROZEN_SURFACE_IDS = [
  "agent_orchestrator",
  "automation_engine",
  "operational_actions",
  "ai_upload_pipeline",
  "workflow_runs",
  "autonomous_recovery_agents",
  "upload_legacy",
  "reviews_global",
  "actions_global",
  "escalations_global",
  "tenants_manager",
  "alerts_global",
  "automation_ui",
  "dead_letters",
  "reviews_project",
] as const;

export type QCFrozenSurfaceId = (typeof QC_FROZEN_SURFACE_IDS)[number];

export type QCFrozenSurface = {
  id: QCFrozenSurfaceId;
  labelHe: string;
  category: QCFreezeCategory;
  uiRoutes: readonly string[];
  apiPrefixes: readonly string[];
  qcReplacement: string | null;
};

export const QC_FROZEN_SURFACES: readonly QCFrozenSurface[] = [
  {
    id: "agent_orchestrator",
    labelHe: "Agent Orchestrator",
    category: "FROZEN",
    uiRoutes: [],
    apiPrefixes: ["/agent/run"],
    qcReplacement: "דוחות שטח + materialization",
  },
  {
    id: "automation_engine",
    labelHe: "מנוע אוטומציה",
    category: "FROZEN",
    uiRoutes: ["/automation"],
    apiPrefixes: ["/automation/"],
    qcReplacement: "התראות ידניות (שלב 4.3)",
  },
  {
    id: "operational_actions",
    labelHe: "פעולות תפעוליות",
    category: "FROZEN",
    uiRoutes: ["/actions"],
    apiPrefixes: ["/actions/"],
    qcReplacement: "quality_issues lifecycle",
  },
  {
    id: "ai_upload_pipeline",
    labelHe: "העלאת דוח → findings",
    category: "FROZEN",
    uiRoutes: ["/upload"],
    apiPrefixes: ["/reports/upload", "/reports/upload/bulk"],
    qcReplacement: "דוחות שטח + registry (שלב 5.7)",
  },
  {
    id: "workflow_runs",
    labelHe: "היסטוריית workflow",
    category: "FROZEN",
    uiRoutes: [],
    apiPrefixes: ["/workflow-runs"],
    qcReplacement: null,
  },
  {
    id: "autonomous_recovery_agents",
    labelHe: "סוכני recovery אוטונומיים",
    category: "FROZEN",
    uiRoutes: [],
    apiPrefixes: [],
    qcReplacement: null,
  },
  {
    id: "upload_legacy",
    labelHe: "העלאת דוח",
    category: "DEPRECATED",
    uiRoutes: ["/upload"],
    apiPrefixes: ["/reports/upload"],
    qcReplacement: "field_visit_reports",
  },
  {
    id: "reviews_global",
    labelHe: "ביקורות AI (גלובלי)",
    category: "DEPRECATED",
    uiRoutes: ["/reviews"],
    apiPrefixes: ["/reviews/"],
    qcReplacement: "ליקויים + דוחות שטח",
  },
  {
    id: "actions_global",
    labelHe: "פעולות תפעוליות",
    category: "DEPRECATED",
    uiRoutes: ["/actions"],
    apiPrefixes: ["/actions/"],
    qcReplacement: "quality_issues",
  },
  {
    id: "escalations_global",
    labelHe: "נקודות סיכון",
    category: "DEPRECATED",
    uiRoutes: ["/escalations"],
    apiPrefixes: ["/actions/escalations"],
    qcReplacement: "quality_issues",
  },
  {
    id: "tenants_manager",
    labelHe: "מנהל דיירים",
    category: "DEPRECATED",
    uiRoutes: ["/tenants"],
    apiPrefixes: [],
    qcReplacement: null,
  },
  {
    id: "alerts_global",
    labelHe: "התראות",
    category: "DEPRECATED",
    uiRoutes: ["/alerts"],
    apiPrefixes: [],
    qcReplacement: "התראות QC (שלב 4.3)",
  },
  {
    id: "automation_ui",
    labelHe: "אוטומציה",
    category: "ADMIN_ONLY",
    uiRoutes: ["/automation"],
    apiPrefixes: ["/automation/"],
    qcReplacement: null,
  },
  {
    id: "dead_letters",
    labelHe: "Dead Letters",
    category: "ADMIN_ONLY",
    uiRoutes: ["/automation/dead-letters"],
    apiPrefixes: [],
    qcReplacement: null,
  },
  {
    id: "reviews_project",
    labelHe: "ביקורות AI (פרויקט)",
    category: "SECONDARY",
    uiRoutes: [],
    apiPrefixes: ["/reviews/"],
    qcReplacement: "ליקויים בפרויקט",
  },
];

export const QC_ALLOWED_EXCEPTIONS = new Set([
  "NotificationTool",
  "QcNotificationService",
  "field_report_catalog_parser",
  "ReportProcessingService",
]);

const surfacesById = new Map(
  QC_FROZEN_SURFACES.map((surface) => [surface.id, surface])
);

const deprecatedUiRoutes = new Set(
  QC_FROZEN_SURFACES.filter((surface) => surface.category === "DEPRECATED")
    .flatMap((surface) => surface.uiRoutes)
);

const frozenApiPrefixes = QC_FROZEN_SURFACES.filter(
  (surface) => surface.category === "FROZEN"
).flatMap((surface) => surface.apiPrefixes);

export function getFrozenSurface(
  surfaceId: string
): QCFrozenSurface | undefined {
  return surfacesById.get(surfaceId as QCFrozenSurfaceId);
}

export function isFrozenSurface(surfaceId: string): boolean {
  const surface = getFrozenSurface(surfaceId);
  return surface?.category === "FROZEN";
}

export function isDeprecatedRoute(href: string): boolean {
  const normalized = (href || "").trim().replace(/\/+$/, "") || "/";
  return deprecatedUiRoutes.has(normalized);
}

export function isFrozenApiPath(path: string): boolean {
  const normalized = (path || "").trim();
  return frozenApiPrefixes.some(
    (prefix) =>
      normalized === prefix || normalized.startsWith(prefix)
  );
}

export function listSurfacesByCategory(
  category: QCFreezeCategory
): QCFrozenSurface[] {
  return QC_FROZEN_SURFACES.filter(
    (surface) => surface.category === category
  );
}

export function isAllowedQcException(componentName: string): boolean {
  return QC_ALLOWED_EXCEPTIONS.has(componentName);
}

export class QCFrozenFeatureError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "QCFrozenFeatureError";
  }
}

/** Guard for CI and development - frozen surfaces must not gain new features. */
export function assertNotFrozenForFeature(surfaceId: string): void {
  if (!isFrozenSurface(surfaceId)) {
    return;
  }

  const surface = getFrozenSurface(surfaceId);
  let message = `QC freeze: surface '${surfaceId}' is frozen`;
  if (surface?.qcReplacement) {
    message += `; use ${surface.qcReplacement} instead`;
  }
  throw new QCFrozenFeatureError(message);
}

export function getFrozenSurfaceForApiPath(
  path: string
): QCFrozenSurface | undefined {
  const normalized = (path || "").trim();

  for (const surface of QC_FROZEN_SURFACES) {
    if (surface.category !== "FROZEN") {
      continue;
    }

    for (const prefix of surface.apiPrefixes) {
      if (normalized === prefix || normalized.startsWith(prefix)) {
        return surface;
      }
    }
  }

  return undefined;
}

/** Aligns with QC_DEPRECATED_PRIMARY_ROUTES in qc-navigation.ts */
export function shouldHideFromPrimaryNav(href: string): boolean {
  return isDeprecatedRoute(href);
}
