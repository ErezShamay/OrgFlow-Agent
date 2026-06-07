const REPORT_UPLOAD_ERROR_MESSAGES: Record<string, string> = {
  UNSUPPORTED_FILE_TYPE:
    "סוג הקובץ אינו נתמך. השתמש ב-PDF, Word, Excel, CSV, טקסט או תמונה.",
  FILE_TOO_LARGE: "הקובץ גדול מדי (מקסימום 10MB).",
  CORRUPTED_PDF: "קובץ PDF פגום או לא שלם.",
  MALWARE_DETECTED: "הקובץ נדחה מסיבות אבטחה.",
  EMPTY_FILE: "הקובץ ריק.",
  FILE_NOT_FOUND: "הקובץ לא נמצא בשרת.",
  FILE_READ_ERROR: "לא ניתן לקרוא את הקובץ.",
  REPORT_PROCESSING_FAILED: "עיבוד הדוח נכשל בשרת.",
};

type ApiErrorPayload = {
  detail?:
    | string
    | {
        error_code?: string;
        message?: string;
      };
  error?: {
    message?: string;
    code?: string;
  };
  message?: string;
};

export async function readApiErrorMessage(
  response: Response,
  fallback: string,
  errorCodeMessages: Record<string, string> = REPORT_UPLOAD_ERROR_MESSAGES
): Promise<string> {
  if (response.status === 403) {
    return "אין הרשאה לבצע פעולה זו";
  }

  if (response.status === 404) {
    return "הפרויקט לא נמצא";
  }

  try {
    const payload = (await response.json()) as ApiErrorPayload;
    const detail = payload.detail;

    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }

    if (detail && typeof detail === "object") {
      const errorCode = detail.error_code?.trim();
      if (errorCode && errorCodeMessages[errorCode]) {
        return errorCodeMessages[errorCode];
      }

      if (detail.message?.trim()) {
        return detail.message;
      }
    }

    const middlewareMessage = payload.error?.message?.trim();
    if (middlewareMessage) {
      return middlewareMessage;
    }

    if (payload.message?.trim()) {
      return payload.message;
    }
  } catch {
    // Response body is not JSON.
  }

  return `${fallback} (${response.status})`;
}

export function normalizeProjectList(payload: unknown): Array<{ id: string; project_name: string }> {
  const projectList = Array.isArray(payload)
    ? payload
    : (payload as { projects?: unknown[] })?.projects || [];

  return (projectList as Array<Record<string, unknown>>)
    .map((project) => ({
      id: String(project.id ?? ""),
      project_name: String(project.project_name ?? project.id ?? "פרויקט"),
    }))
    .filter((project) => project.id);
}
