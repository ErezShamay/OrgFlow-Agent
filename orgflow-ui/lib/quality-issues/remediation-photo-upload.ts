import { apiFetch } from "@/lib/api/client";
import { readApiErrorMessage } from "@/lib/api/read-error-message";
import {
  buildIssuePhotosPath,
  QualityIssueApiError,
} from "@/lib/quality-issues/api";
import { remediationPhotoFilename } from "@/lib/quality-issues/remediation-photo";

export type RemediationPhotoUploadResult = {
  issueId: string;
  photoId: string;
  url: string;
};

async function parseRemediationPhotoError(
  response: Response,
  fallback: string
): Promise<never> {
  const message = await readApiErrorMessage(response, fallback);
  throw new QualityIssueApiError(message, response.status);
}

export async function uploadRemediationPhoto(
  issueId: string,
  file: Blob
): Promise<RemediationPhotoUploadResult> {
  const formData = new FormData();
  const mimeType = file.type || "image/jpeg";
  formData.append(
    "file",
    file,
    remediationPhotoFilename(mimeType)
  );

  const response = await apiFetch(buildIssuePhotosPath(issueId), {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    return parseRemediationPhotoError(
      response,
      "העלאת תמונת התיקון נכשלה"
    );
  }

  const body = (await response.json()) as {
    issue_id: string;
    photo_id: string;
    url: string;
  };

  return {
    issueId: body.issue_id,
    photoId: body.photo_id,
    url: body.url,
  };
}
