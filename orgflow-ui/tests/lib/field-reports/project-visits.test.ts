import { describe, expect, it } from "vitest";

import {
  buildProjectFieldVisitsPath,
  parseProjectFieldVisitListResponse,
} from "@/lib/field-reports/project-visits";

describe("project field visit list client", () => {
  it("builds visits path filtered by project", () => {
    expect(buildProjectFieldVisitsPath("proj 1")).toBe(
      "/field-reports/visits?project_id=proj+1"
    );
  });

  it("parses visit list payload", () => {
    const parsed = parseProjectFieldVisitListResponse({
      reports: [
        {
          id: "report-1",
          project_id: "proj-1",
          visit_date: "2026-06-01",
          visit_type_label_he: "שלד",
          status: "CLOSED",
          status_label_he: "סגור",
        },
        { id: "bad" },
      ],
    });

    expect(parsed.reports).toEqual([
      {
        id: "report-1",
        project_id: "proj-1",
        visit_date: "2026-06-01",
        visit_type_label_he: "שלד",
        status: "CLOSED",
        status_label_he: "סגור",
      },
    ]);
  });
});
