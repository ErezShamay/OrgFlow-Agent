import { describe, expect, it } from "vitest";

import {
  buildPeriodicReportCsv,
  formatPeriodicReportPeriod,
} from "@/lib/quality-issues/periodic-report";
import type { QualityPeriodicReportResponse } from "@/lib/quality-issues/types";

const sampleReport: QualityPeriodicReportResponse = {
  organization_id: "org-1",
  project_id: null,
  period_days: 30,
  period_start: "2026-05-10T00:00:00.000Z",
  period_end: "2026-06-10T00:00:00.000Z",
  generated_at: "2026-06-10T00:00:00.000Z",
  summary: {
    total_issues: 2,
    open_total: 1,
    open_critical: 1,
    closed_total: 1,
    recurring_total: 0,
  },
  projects: [
    {
      project_id: "proj-1",
      project_name: "האורנים 7",
      contractor_name: "קבלנות כהן",
      issue_total: 2,
      open_total: 1,
      open_critical: 1,
      recurring_total: 0,
    },
  ],
  issues: [
    {
      issue_id: "issue-1",
      title: "נזילה",
      project_id: "proj-1",
      project_name: "האורנים 7",
      contractor_name: "קבלנות כהן",
      status: "OPEN",
      severity: "CRITICAL",
      trade: "אינסטלציה",
      location: "קומה 2",
      standard_ref: 'ת"י 1205',
      catalog_issue_id: "QC-MEP-001",
      recurrence_count: 0,
      first_seen_at: "2026-06-01T00:00:00.000Z",
      last_seen_at: "2026-06-05T00:00:00.000Z",
    },
  ],
};

describe("periodic report helpers", () => {
  it("formats report period in Hebrew locale", () => {
    expect(formatPeriodicReportPeriod(sampleReport)).toContain("2026");
  });

  it("builds CSV with BOM and Hebrew headers", () => {
    const csv = buildPeriodicReportCsv(sampleReport);
    expect(csv.startsWith("\uFEFF")).toBe(true);
    expect(csv).toContain("דוח תקופתי");
    expect(csv).toContain("נזילה");
    expect(csv).toContain("האורנים 7");
  });
});
