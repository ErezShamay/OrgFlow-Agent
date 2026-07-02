import { describe, expect, it } from "vitest";

import {
  buildSupervisionChecklist,
  filterSupervisionCatalogIssues,
  isSupervisionChecklistReport,
  matchesSupervisionCatalogIssue,
} from "@/lib/field-reports/supervision-checklist-builder";
import type { SupervisionCatalog } from "@/lib/field-reports/schema/types";

const sampleCatalog: SupervisionCatalog = {
  catalog_version: "1.4.0-supervision-checklist",
  issues: [
    {
      issue_id: "QC-STR-001",
      issue_name_he: "כיסוי בטון",
      standard_ref: 'ת"י 466 חלק 1',
      top_family: "STRUCTURAL_WORKS",
      category_id: "REINFORCEMENT_STEEL",
      category_name_he: "ברזל זיון",
      scope: "BOTH",
      allowed_stages: ["STRUCTURE"],
    },
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
      issue_id: "SUP-FIN-007",
      issue_name_he: "מדרגות חלקות",
      standard_ref: 'ת"י 1555',
      top_family: "FINISHING_WORKS",
      category_id: "INTERIOR_SYSTEMS",
      category_name_he: "מדרגות",
      scope: "PUBLIC_AREA",
      public_area_id: "ELEVATOR_STAIRS",
      allowed_stages: ["FINISHING"],
    },
    {
      issue_id: "SUP-MEP-006",
      issue_name_he: "גלאי עשן",
      standard_ref: 'ת"י 1220',
      top_family: "MECHANICAL_ELECTRICAL_SYSTEMS",
      category_id: "FIRE_SAFETY_SYSTEMS",
      category_name_he: "בטיחות",
      scope: "BOTH",
      allowed_stages: ["FINISHING"],
    },
  ],
};

describe("filterSupervisionCatalogIssues", () => {
  it("filters apartment finishing items", () => {
    const filtered = filterSupervisionCatalogIssues({
      catalog: sampleCatalog,
      constructionStage: "FINISHING",
      visitScope: "APARTMENT",
    });

    expect(filtered.map((issue) => issue.issue_id).sort()).toEqual([
      "SUP-FIN-004",
      "SUP-MEP-006",
    ]);
  });

  it("filters structure stage items", () => {
    const filtered = filterSupervisionCatalogIssues({
      catalog: sampleCatalog,
      constructionStage: "STRUCTURE",
      visitScope: "APARTMENT",
    });

    expect(filtered.map((issue) => issue.issue_id)).toEqual(["QC-STR-001"]);
  });

  it("includes all stages when construction stage is MIXED", () => {
    const filtered = filterSupervisionCatalogIssues({
      catalog: sampleCatalog,
      constructionStage: "MIXED",
      visitScope: "APARTMENT",
    });

    expect(filtered.map((issue) => issue.issue_id).sort()).toEqual([
      "QC-STR-001",
      "SUP-FIN-004",
      "SUP-MEP-006",
    ]);
  });

  it("includes apartment and public area items for whole building scope", () => {
    const filtered = filterSupervisionCatalogIssues({
      catalog: sampleCatalog,
      constructionStage: "FINISHING",
      visitScope: "WHOLE_BUILDING",
    });

    expect(filtered.map((issue) => issue.issue_id).sort()).toEqual([
      "SUP-FIN-004",
      "SUP-FIN-007",
      "SUP-MEP-006",
    ]);
  });

  it("filters public area by public_area_id", () => {
    const lobbyOnly = filterSupervisionCatalogIssues({
      catalog: sampleCatalog,
      constructionStage: "FINISHING",
      visitScope: "PUBLIC_AREA",
      publicAreaId: "LOBBY",
    });

    expect(lobbyOnly.map((issue) => issue.issue_id)).toEqual(["SUP-MEP-006"]);

    const stairs = filterSupervisionCatalogIssues({
      catalog: sampleCatalog,
      constructionStage: "FINISHING",
      visitScope: "PUBLIC_AREA",
      publicAreaId: "ELEVATOR_STAIRS",
    });

    expect(stairs.map((issue) => issue.issue_id).sort()).toEqual([
      "SUP-FIN-007",
      "SUP-MEP-006",
    ]);
  });
});

describe("buildSupervisionChecklist", () => {
  it("builds supervision_checklist block with stable item ids", () => {
    const block = buildSupervisionChecklist({
      catalog: sampleCatalog,
      constructionStage: "FINISHING",
      visitScope: "APARTMENT",
      apartmentNumber: "12",
    });

    expect(block.kind).toBe("supervision_checklist");
    expect(block.title_he).toBe("ביקור דירה 12");
    expect(block.construction_stage).toBe("FINISHING");
    expect(block.visit_scope).toBe("APARTMENT");
    expect(block.apartment_number).toBe("12");
    expect(block.items).toHaveLength(2);
    expect(block.items[0]).toMatchObject({
      id: "checklist-SUP-FIN-004",
      catalog_issue_id: "SUP-FIN-004",
      status: "UNCHECKED",
      photo_ids: [],
      standard_ref: 'ת"י 1555',
    });
  });

  it("uses public area title for public scope", () => {
    const block = buildSupervisionChecklist({
      catalog: sampleCatalog,
      constructionStage: "FINISHING",
      visitScope: "PUBLIC_AREA",
      publicAreaId: "ELEVATOR_STAIRS",
    });

    expect(block.title_he).toBe("ביקור מעליות / חדרי מדרגות");
    expect(block.public_area_id).toBe("ELEVATOR_STAIRS");
    expect(block.items.map((item) => item.catalog_issue_id).sort()).toEqual([
      "SUP-FIN-007",
      "SUP-MEP-006",
    ]);
  });
});

describe("matchesSupervisionCatalogIssue", () => {
  it("rejects finishing item on structure stage", () => {
    const issue = sampleCatalog.issues[1];

    expect(
      matchesSupervisionCatalogIssue({
        issue,
        constructionStage: "STRUCTURE",
        visitScope: "APARTMENT",
      })
    ).toBe(false);
  });
});

describe("isSupervisionChecklistReport", () => {
  it("detects supervision_checklist blocks without breaking legacy checklist", () => {
    expect(
      isSupervisionChecklistReport([
        { kind: "checklist" },
        { kind: "findings_table" },
      ])
    ).toBe(false);

    expect(
      isSupervisionChecklistReport([{ kind: "supervision_checklist" }])
    ).toBe(true);
  });
});
