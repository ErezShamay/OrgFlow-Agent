export const EMAIL_INVALID_MESSAGE =
  "כתובת אימייל לא תקינה. יש להזין בפורמט name@domain.com";

const EMAIL_PATTERN =
  /^[A-Za-z0-9._%+-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$/;

const MAX_EMAIL_LENGTH = 320;

export const PROJECT_EMAIL_FIELDS = [
  "developer_email",
  "contractor_email",
  "developer_pm_email",
  "lawyer_email",
  "accompanying_lawyer_email",
  "supervisor_email",
  "architect_email",
  "site_manager_email",
] as const;

export type ProjectEmailField = (typeof PROJECT_EMAIL_FIELDS)[number];

export function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

export function isValidEmail(email: string): boolean {
  const candidate = email.trim();
  if (!candidate || candidate.length > MAX_EMAIL_LENGTH) {
    return false;
  }

  return EMAIL_PATTERN.test(candidate);
}

export function validateEmail(email: string): string | null {
  if (!isValidEmail(email)) {
    return EMAIL_INVALID_MESSAGE;
  }

  return null;
}

export function validateOptionalEmail(email: string): string | null {
  const trimmed = email.trim();
  if (!trimmed) {
    return null;
  }

  return validateEmail(trimmed);
}

export function validateProjectEmails(
  form: Record<string, string>,
  fields: readonly string[] = PROJECT_EMAIL_FIELDS
): string | null {
  for (const field of fields) {
    const error = validateEmail(form[field] ?? "");
    if (error) {
      return error;
    }
  }

  return null;
}

export function validateOptionalProjectEmails(
  form: Record<string, string>,
  fields: readonly string[] = PROJECT_EMAIL_FIELDS
): string | null {
  for (const field of fields) {
    const error = validateOptionalEmail(form[field] ?? "");
    if (error) {
      return error;
    }
  }

  return null;
}
