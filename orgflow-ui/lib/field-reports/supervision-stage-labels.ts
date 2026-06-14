import type {
  ConstructionStage,
  VisitScope,
} from "@/lib/field-reports/schema/types";

export const CONSTRUCTION_STAGE_LABELS: Record<ConstructionStage, string> = {
  STRUCTURE: "שלד",
  FINISHING: "גמר",
  MIXED: "משולב",
};

export const VISIT_SCOPE_LABELS: Record<VisitScope, string> = {
  APARTMENT: "דירה",
  PUBLIC_AREA: "שטחים ציבוריים",
};

export function constructionStageLabelHe(stage: ConstructionStage): string {
  return CONSTRUCTION_STAGE_LABELS[stage];
}

export function visitScopeLabelHe(scope: VisitScope): string {
  return VISIT_SCOPE_LABELS[scope];
}
