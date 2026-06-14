import { apiFetch } from "@/lib/api/client";
import { listChecklistPhotosForItem } from "@/lib/field-reports/checklist-photo-store";
import { listLinePhotosForLine } from "@/lib/field-reports/line-photo-store";
import type { SupervisionChecklistItem } from "@/lib/field-reports/schema/types";

import type { ChecklistPhotoData, LinePhotoData, PdfReportLine } from "./types";

async function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      resolve(String(reader.result || ""));
    };
    reader.onerror = () => {
      reject(reader.error ?? new Error("Failed to read image blob"));
    };
    reader.readAsDataURL(blob);
  });
}

async function fetchRemoteImageDataUrl(url: string): Promise<string | null> {
  try {
    const response = await apiFetch(url);
    if (!response.ok) {
      return null;
    }
    const blob = await response.blob();
    return blobToDataUrl(blob);
  } catch {
    return null;
  }
}

export async function resolveLinePhotos(
  reportId: string,
  lines: PdfReportLine[]
): Promise<LinePhotoData[]> {
  const photos: LinePhotoData[] = [];

  for (const line of lines) {
    const remotePhotos =
      line.photos?.length
        ? line.photos
        : line.photo_url
          ? [{ id: line.photo_ids?.[0] ?? "legacy", url: line.photo_url }]
          : [];

    const localPhotos = await listLinePhotosForLine(reportId, line.id);

    for (const local of localPhotos) {
      photos.push({
        lineId: line.id,
        photoId: local.photoId,
        dataUrl: await blobToDataUrl(local.blob),
      });
    }

    for (const remote of remotePhotos) {
      if (
        localPhotos.some((local) => local.photoId === remote.id)
      ) {
        continue;
      }

      const dataUrl = await fetchRemoteImageDataUrl(remote.url);
      if (dataUrl) {
        photos.push({
          lineId: line.id,
          photoId: remote.id,
          dataUrl,
        });
      }
    }
  }

  return photos;
}

export async function resolveChecklistPhotos(
  reportId: string,
  items: SupervisionChecklistItem[]
): Promise<ChecklistPhotoData[]> {
  const photos: ChecklistPhotoData[] = [];

  for (const item of items) {
    const localPhotos = await listChecklistPhotosForItem(reportId, item.id);

    for (const local of localPhotos) {
      photos.push({
        checklistItemId: item.id,
        photoId: local.photoId,
        dataUrl: await blobToDataUrl(local.blob),
      });
    }
  }

  return photos;
}

export async function resolveRemoteImageDataUrl(
  imageUrl: string | null | undefined
): Promise<string | null> {
  if (!imageUrl) {
    return null;
  }

  if (imageUrl.startsWith("data:")) {
    return imageUrl;
  }

  if (imageUrl.startsWith("/")) {
    return fetchRemoteImageDataUrl(imageUrl);
  }

  try {
    const response = await fetch(imageUrl);
    if (!response.ok) {
      return null;
    }
    return blobToDataUrl(await response.blob());
  } catch {
    return null;
  }
}

export async function resolveLogoDataUrl(
  logoUrl: string | null | undefined
): Promise<string | null> {
  return resolveRemoteImageDataUrl(logoUrl);
}

export async function resolveIllustrationDataUrl(
  headerFields: Record<string, unknown>
): Promise<string | null> {
  const metadata = headerFields.project_metadata;
  const nestedUrl =
    metadata
    && typeof metadata === "object"
    && !Array.isArray(metadata)
    && typeof (metadata as Record<string, unknown>).illustration_url === "string"
      ? String((metadata as Record<string, unknown>).illustration_url).trim()
      : "";

  const flatUrl =
    typeof headerFields.illustration_url === "string"
      ? headerFields.illustration_url.trim()
      : "";

  return resolveRemoteImageDataUrl(nestedUrl || flatUrl || null);
}
