import "fake-indexeddb/auto";

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import { isSupervisionChecklistReport } from "@/lib/field-reports/supervision-checklist-builder";
import {
  createSupervisionLocalReport,
  deriveVisitTypeFromConstructionStage,
} from "@/lib/field-reports/supervision-new-report";
import type { SupervisionCatalog } from "@/lib/field-reports/schema/types";

const sampleCatalog: SupervisionCatalog = {
  catalog_version: "1.4.0-supervision-checklist",
  issues: [
    {
      issue_id: "SUP-FIN-004",
      issue_name_he: "פוגות",
      standard_ref: 'ת"י 1555',
      top_family: "FINISHING_WORKS",
      category_id: "TILING",
      category_name_he: "ריצוף",
      scope: "APARTMENT",
      allowed_stages: ["FINISHING"],
    },
    {
      issue_id: "SUP-FIN-009",
      issue_name_he: "ריצוף לובי",
      standard_ref: 'ת"י 1928',
      top_family: "FINISHING_WORKS",
      category_id: "TILING",
      category_name_he: "ריצוף",
      scope: "PUBLIC_AREA",
      public_area_id: "LOBBY",
      allowed_stages: ["FINISHING"],
    },
  ],
};

describe("deriveVisitTypeFromConstructionStage", () => {
  it("maps construction stages to visit_type (§10.3)", () => {
    expect(deriveVisitTypeFromConstructionStage("STRUCTURE")).toBe(
      "STRUCTURE_SITE"
    );
    expect(deriveVisitTypeFromConstructionStage("FINISHING")).toBe(
      "FINISHING_APARTMENTS"
    );
    expect(deriveVisitTypeFromConstructionStage("MIXED")).toBe("MIXED");
  });
});

describe("createSupervisionLocalReport", () => {
  beforeEach(async () => {
    await deleteFieldReportDatabase();
  });

  afterEach(async () => {
    await closeFieldReportDatabase();
    await deleteFieldReportDatabase();
  });

  it("persists supervision_checklist block and supervision_meta", async () => {
    const report = await createSupervisionLocalReport({
      organizationId: "org-1",
      projectId: "proj-1",
      projectName: "פרויקט בדיקה",
      visitDate: "2026-06-14",
      catalog: sampleCatalog,
      constructionStage: "FINISHING",
      visitScope: "APARTMENT",
      apartmentNumber: "12",
      apartmentId: "apt-1",
    });

    expect(report.visit_type).toBe("FINISHING_APARTMENTS");
    expect(report.header_fields?.supervision_meta).toMatchObject({
      construction_stage: "FINISHING",
      visit_scope: "APARTMENT",
      apartment_number: "12",
    });

    const blocks = report.header_fields?.blocks as Array<{ kind?: string }>;
    expect(isSupervisionChecklistReport(blocks)).toBe(true);
    expect(
      blocks?.some((block) => block.kind === "supervision_checklist")
    ).toBe(true);
  });

  it("creates summary and per-apartment checklists for multi-apartment visit", async () => {
    const report = await createSupervisionLocalReport({
      organizationId: "org-1",
      projectId: "proj-1",
      projectName: "פרויקט בדיקה",
      visitDate: "2026-06-14",
      catalog: sampleCatalog,
      constructionStage: "FINISHING",
      visitScope: "MULTI_APARTMENT",
      visitedApartments: [
        { apartment_id: "apt-1", apartment_number: "3" },
        { apartment_id: "apt-2", apartment_number: "5" },
      ],
    });

    expect(report.header_fields?.supervision_meta).toMatchObject({
      visit_scope: "MULTI_APARTMENT",
      visited_apartments: [
        { apartment_id: "apt-1", apartment_number: "3" },
        { apartment_id: "apt-2", apartment_number: "5" },
      ],
    });

    const blocks = report.header_fields?.blocks as Array<{
      kind?: string;
      title_he?: string;
      body_he?: string;
    }>;
    expect(blocks?.find((block) => block.kind === "free_text")?.body_he).toContain(
      "2 דירות"
    );
    expect(
      blocks?.filter((block) => block.kind === "supervision_checklist")
    ).toHaveLength(2);
  });
});
