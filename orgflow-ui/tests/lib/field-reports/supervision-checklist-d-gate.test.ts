/**
 * Gate — שלב D (field-supervision-checklist-spec §16.D).
 * עורך צ'קליסט + תמונות offline (מקס 3).
 */
import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

const UI_ROOT = path.resolve(__dirname, "../../..");

function readSource(relativePath: string): string {
  return readFileSync(path.join(UI_ROOT, relativePath), "utf8");
}

describe("supervision checklist stage D gate (§16.D)", () => {
  it("SupervisionChecklistEditor exists with status controls and photos", () => {
    const editor = readSource(
      "components/field-reports/SupervisionChecklistEditor.tsx"
    );

    expect(editor).toContain("ChecklistItemPhotoCapture");
    expect(editor).toContain("CHECKLIST_ITEM_STATUS_OPTIONS");
    expect(editor).toContain("groupSupervisionChecklistItems");
  });

  it("VisitReportEditor integrates supervision checklist editor", () => {
    const page = readSource("components/field-reports/VisitReportEditor.tsx");

    expect(page).toContain("SupervisionChecklistEditor");
    expect(page).toContain("isSupervisionChecklistReport");
  });

  it("checklist photo store supports offline blobs with max 3", () => {
    const store = readSource("lib/field-reports/checklist-photo-store.ts");
    const constants = readSource(
      "lib/field-reports/checklist-photo-constants.ts"
    );
    const schema = readSource("lib/field-reports/db/schema.ts");

    expect(constants).toContain("MAX_CHECKLIST_ITEM_PHOTOS = 3");
    expect(store).toContain("saveChecklistPhotoLocally");
    expect(store).toContain("listPendingChecklistPhotos");
    expect(schema).toContain('"checklist_photo"');
  });

  it("sync-pending-photos.ts includes checklist pending count", () => {
    const sync = readSource("lib/field-reports/sync-pending-photos.ts");

    expect(sync).toContain("listPendingChecklistPhotos");
    expect(sync).toContain("checklist_pending");
  });

  it("ChecklistItemPhotoCapture saves locally without requiring network", () => {
    const capture = readSource(
      "components/field-reports/ChecklistItemPhotoCapture.tsx"
    );

    expect(capture).toContain("saveChecklistPhotoLocally");
    expect(capture).toContain("pendingUpload: true");
    expect(capture).toContain("MAX_CHECKLIST_ITEM_PHOTOS");
  });
});
