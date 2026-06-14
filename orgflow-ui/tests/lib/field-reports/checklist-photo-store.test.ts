import "fake-indexeddb/auto";

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  canAddChecklistPhoto,
  countChecklistPhotosLocally,
  deleteChecklistPhotoLocally,
  listChecklistPhotosForItem,
  listPendingChecklistPhotos,
  MAX_CHECKLIST_ITEM_PHOTOS,
  saveChecklistPhotoLocally,
} from "@/lib/field-reports/checklist-photo-store";
import {
  closeFieldReportDatabase,
  deleteFieldReportDatabase,
} from "@/lib/field-reports/db/field-report-db";

const REPORT_ID = "report-1";
const ITEM_ID = "checklist-SUP-FIN-004";

describe("checklist-photo-store", () => {
  beforeEach(async () => {
    await deleteFieldReportDatabase();
  });

  afterEach(async () => {
    await closeFieldReportDatabase();
    await deleteFieldReportDatabase();
  });

  it("saves photos offline with pending_upload", async () => {
    const blob = new Blob(["photo"], { type: "image/jpeg" });
    const photoId = await saveChecklistPhotoLocally(
      REPORT_ID,
      ITEM_ID,
      blob,
      { pendingUpload: true, photoId: "primary" }
    );

    expect(photoId).toBe("primary");

    const photos = await listChecklistPhotosForItem(REPORT_ID, ITEM_ID);
    expect(photos).toHaveLength(1);
    expect(photos[0]?.pendingUpload).toBe(true);

    const pending = await listPendingChecklistPhotos(REPORT_ID);
    expect(pending).toHaveLength(1);
  });

  it("enforces max 3 photos per checklist item", async () => {
    const blob = new Blob(["photo"], { type: "image/jpeg" });

    for (const slot of ["primary", "2", "3"] as const) {
      await saveChecklistPhotoLocally(REPORT_ID, ITEM_ID, blob, {
        pendingUpload: true,
        photoId: slot,
      });
    }

    const count = await countChecklistPhotosLocally(REPORT_ID, ITEM_ID);
    expect(count).toBe(MAX_CHECKLIST_ITEM_PHOTOS);
    expect(canAddChecklistPhoto(count)).toBe(false);
  });

  it("deletes checklist photo blobs locally", async () => {
    const blob = new Blob(["photo"], { type: "image/jpeg" });
    await saveChecklistPhotoLocally(REPORT_ID, ITEM_ID, blob, {
      pendingUpload: true,
      photoId: "primary",
    });

    await deleteChecklistPhotoLocally(REPORT_ID, ITEM_ID, "primary");

    expect(await countChecklistPhotosLocally(REPORT_ID, ITEM_ID)).toBe(0);
  });
});
