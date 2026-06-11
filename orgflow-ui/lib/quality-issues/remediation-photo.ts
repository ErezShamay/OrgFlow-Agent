export function remediationPhotoFilename(mimeType: string): string {
  if (mimeType === "image/png") {
    return "remediation.png";
  }
  if (mimeType === "image/webp") {
    return "remediation.webp";
  }
  return "remediation.jpg";
}

export function canSubmitRemediation(input: {
  photoIds: string[];
}): boolean {
  return input.photoIds.length > 0;
}
