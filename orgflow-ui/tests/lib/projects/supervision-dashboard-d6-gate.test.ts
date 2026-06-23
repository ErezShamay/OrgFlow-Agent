/**
 * Gate D6 — «תיעוד ביקור» deep-link prefill from project dashboard.
 */
import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import {
  hasSupervisionNewReportApartmentPrefill,
  parseSupervisionNewReportPrefill,
  resolveApartmentSelectionFromPrefill,
} from "@/lib/field-reports/supervision-new-report";
import { projectSupervisionVisitReportPath } from "@/lib/projects/supervision-dashboard";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readUiSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("supervision dashboard D6 gate", () => {
  it("parses apartment_number and apartment_id query params", () => {
    const params = new URLSearchParams(
      "apartment_number=6&apartment_id=apt-6"
    );

    expect(parseSupervisionNewReportPrefill(params)).toEqual({
      apartmentNumber: "6",
      apartmentId: "apt-6",
    });
    expect(hasSupervisionNewReportApartmentPrefill({
      apartmentNumber: "6",
      apartmentId: null,
    })).toBe(true);
  });

  it("resolves apartment selection by id or number", () => {
    const apartments = [
      {
        id: "apt-6",
        apartment_number: "6",
        owner_name: "ישראל ישראלי",
      },
    ];

    expect(
      resolveApartmentSelectionFromPrefill(apartments, {
        apartmentNumber: null,
        apartmentId: "apt-6",
      })
    ).toMatchObject({
      apartmentId: "apt-6",
      apartmentNumber: "6",
      adHocApartment: false,
    });

    expect(
      resolveApartmentSelectionFromPrefill(apartments, {
        apartmentNumber: "6",
        apartmentId: null,
      })
    ).toMatchObject({
      apartmentNumber: "6",
      adHocApartment: false,
    });
  });

  it("wires dashboard visit link and new-report page prefill", () => {
    const grid = readUiSource(
      "components/projects/ProjectApartmentProgressGrid.tsx"
    );
    const newReportPage = readUiSource(
      "app/(dashboard)/projects/[id]/field-reports/new/page.tsx"
    );
    const lib = readUiSource("lib/field-reports/supervision-new-report.ts");

    expect(projectSupervisionVisitReportPath("proj-1", "6", "apt-6")).toContain(
      "apartment_number=6"
    );
    expect(projectSupervisionVisitReportPath("proj-1", "6", "apt-6")).toContain(
      "apartment_id=apt-6"
    );
    expect(grid).toContain("projectSupervisionVisitReportPath");
    expect(grid).toContain("תיעוד ביקור");
    expect(newReportPage).toContain("parseSupervisionNewReportPrefill");
    expect(newReportPage).toContain("resolveApartmentSelectionFromPrefill");
    expect(newReportPage).toContain('setDocumentKind("WEEKLY_APARTMENT")');
    expect(lib).toContain("supervision_checklist");
    expect(lib).toContain("visit_scope: params.visitScope");
  });
});
