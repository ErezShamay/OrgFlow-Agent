import "fake-indexeddb/auto";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";
import {
  loadVisitReportForPage,
  localVisitReportToView,
  resolveLocalVisitReport,
  resolveVisitReportApiId,
  serverVisitReportId,
} from "@/lib/field-reports/visit-report-view";
import { saveLocalReport } from "@/lib/field-reports/repositories/reports-repository";

vi.mock("@/lib/api/client", () => ({
  apiFetch: vi.fn(),
}));

const ORG_ID = "org-visit-view";
const CLIENT_UUID = "a1111111-1111-4111-8111-111111111111";
const SERVER_ID = "server-report-99";
/** מזהה שרת בפורמט UUID - לא ניתן לבלבל עם `isClientUuid` בלבד. */
const SERVER_UUID = "d4444444-4444-4444-8444-444444444444";

describe("visit-report-view (FR-012)", () => {
  beforeEach(async () => {
    await deleteFieldReportDatabase();
  });

  afterEach(async () => {
    await closeFieldReportDatabase();
    await deleteFieldReportDatabase();
  });

  it("localVisitReportToView maps client uuid and lines", async () => {
    const saved = await saveLocalReport({
      client_report_uuid: CLIENT_UUID,
      organization_id: ORG_ID,
      project_id: "p1",
      project_name: "פרויקט",
      visit_type: "STRUCTURE_SITE",
      visit_type_label_he: "שלד / אתר",
      visit_date: "2026-06-03",
      header_fields: { site_address: "רחוב 1" },
      local_status: "LOCAL_IN_PROGRESS",
      lines: [
        {
          client_line_uuid: "b2222222-2222-4222-8222-222222222222",
          id: "b2222222-2222-4222-8222-222222222222",
          sort_order: 1,
          description: "ממצא",
        },
      ],
    });

    const view = localVisitReportToView(saved);

    expect(view.id).toBe(CLIENT_UUID);
    expect(view.client_report_uuid).toBe(CLIENT_UUID);
    expect(view.is_editable).toBe(true);
    expect(view.lines).toHaveLength(1);
    expect(view.lines[0].id).toBe("b2222222-2222-4222-8222-222222222222");
  });

  it("resolveLocalVisitReport finds by client uuid or server id", async () => {
    await saveLocalReport({
      client_report_uuid: CLIENT_UUID,
      server_report_id: SERVER_ID,
      organization_id: ORG_ID,
      project_id: "p1",
      visit_type: "STRUCTURE_SITE",
      visit_date: "2026-06-03",
      header_fields: {},
    });

    expect(
      (await resolveLocalVisitReport(CLIENT_UUID))?.client_report_uuid
    ).toBe(CLIENT_UUID);
    expect(
      (await resolveLocalVisitReport(SERVER_ID))?.server_report_id
    ).toBe(SERVER_ID);
  });

  it("resolveLocalVisitReport finds by server UUID (Supabase id)", async () => {
    await saveLocalReport({
      client_report_uuid: CLIENT_UUID,
      server_report_id: SERVER_UUID,
      organization_id: ORG_ID,
      project_id: "p1",
      visit_type: "STRUCTURE_SITE",
      visit_date: "2026-06-03",
      header_fields: {},
    });

    expect(
      (await resolveLocalVisitReport(SERVER_UUID))?.client_report_uuid
    ).toBe(CLIENT_UUID);
  });

  it("resolveVisitReportApiId treats route UUID as server id when not local-only", () => {
    expect(resolveVisitReportApiId(SERVER_UUID, null)).toBe(SERVER_UUID);
    expect(
      resolveVisitReportApiId(CLIENT_UUID, {
        client_report_uuid: CLIENT_UUID,
        server_report_id: null,
      } as never)
    ).toBeNull();
  });

  it("loadVisitReportForPage fetches remote IN_PROGRESS report by server UUID", async () => {
    const { apiFetch } = await import("@/lib/api/client");
    vi.mocked(apiFetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        id: SERVER_UUID,
        client_report_uuid: "e5555555-5555-4555-8555-555555555555",
        status: "IN_PROGRESS",
        status_label_he: "בעבודה",
        project_id: "p1",
        visit_type: "STRUCTURE_SITE",
        visit_type_label_he: "שלד",
        visit_date: "2026-06-03",
        header_fields: {},
        lines: [],
        is_editable: true,
      }),
    } as Response);

    const loaded = await loadVisitReportForPage(SERVER_UUID, {
      navigatorOnline: true,
      apiReachable: true,
    });

    expect(loaded.source).toBe("remote");
    expect(loaded.report.id).toBe(SERVER_UUID);
    expect(loaded.report.server_report_id).toBe(SERVER_UUID);
    expect(apiFetch).toHaveBeenCalledWith(
      `/field-reports/visits/${SERVER_UUID}`
    );
  });

  it("localVisitReportToView maps LOCAL_CLOSED as non-editable", async () => {
    const saved = await saveLocalReport({
      client_report_uuid: CLIENT_UUID,
      organization_id: ORG_ID,
      project_id: "p1",
      visit_type: "STRUCTURE_SITE",
      visit_date: "2026-06-03",
      header_fields: {},
      local_status: "LOCAL_CLOSED",
      closed_at: "2026-06-03T12:00:00.000Z",
    });

    const view = localVisitReportToView(saved);
    expect(view.is_editable).toBe(false);
    expect(view.status).toBe("CLOSED");
    expect(view.was_closed).toBe(true);
  });

  it("loadVisitReportForPage returns local report when offline", async () => {
    await saveLocalReport({
      client_report_uuid: CLIENT_UUID,
      organization_id: ORG_ID,
      project_id: "p1",
      visit_type: "STRUCTURE_SITE",
      visit_date: "2026-06-03",
      header_fields: {},
      local_status: "LOCAL_IN_PROGRESS",
    });

    const loaded = await loadVisitReportForPage(CLIENT_UUID, {
      navigatorOnline: false,
      apiReachable: false,
    });

    expect(loaded.source).toBe("local");
    expect(loaded.report.project_id).toBe("p1");
    expect(loaded.dataSource.mode).toBe("local-only");
    expect(serverVisitReportId(loaded.report)).toBeNull();
  });
});
