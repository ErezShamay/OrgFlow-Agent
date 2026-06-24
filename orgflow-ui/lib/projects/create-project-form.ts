import type { ProjectScheme } from "@/lib/field-reports/schema/types";
import { validateProjectEmails } from "@/lib/validation/email";

export type ProjectCreateFormState = {
  project_name: string;
  scheme: ProjectScheme | "";
  city: string;
  floors_count: string;
  housing_units_count: string;
  project_start_date: string;
  project_end_date: string;
  project_grace_end_date: string;
  structure_documentation_date: string;
  developer_name: string;
  developer_email: string;
  contractor_name: string;
  contractor_email: string;
  developer_pm_name: string;
  developer_pm_email: string;
  lawyer_name: string;
  lawyer_email: string;
  accompanying_lawyer: string;
  accompanying_lawyer_email: string;
  supervisor_name: string;
  supervisor_email: string;
  architect_name: string;
  architect_email: string;
  site_manager_name: string;
  site_manager_email: string;
};

export const EMPTY_PROJECT_CREATE_FORM: ProjectCreateFormState = {
  project_name: "",
  scheme: "",
  city: "",
  floors_count: "",
  housing_units_count: "",
  project_start_date: "",
  project_end_date: "",
  project_grace_end_date: "",
  structure_documentation_date: "",
  developer_name: "",
  developer_email: "",
  contractor_name: "",
  contractor_email: "",
  developer_pm_name: "",
  developer_pm_email: "",
  lawyer_name: "",
  lawyer_email: "",
  accompanying_lawyer: "",
  accompanying_lawyer_email: "",
  supervisor_name: "",
  supervisor_email: "",
  architect_name: "",
  architect_email: "",
  site_manager_name: "",
  site_manager_email: "",
};

const REQUIRED_TEXT_FIELDS: ReadonlyArray<keyof ProjectCreateFormState> = [
  "project_name",
  "scheme",
  "city",
  "project_start_date",
  "project_end_date",
  "project_grace_end_date",
  "structure_documentation_date",
  "developer_name",
  "developer_email",
  "contractor_name",
  "contractor_email",
  "developer_pm_name",
  "developer_pm_email",
  "lawyer_name",
  "lawyer_email",
  "accompanying_lawyer",
  "accompanying_lawyer_email",
  "supervisor_name",
  "supervisor_email",
  "architect_name",
  "architect_email",
  "site_manager_name",
  "site_manager_email",
];

export type ProjectCreatePayload = {
  project_name: string;
  scheme: ProjectScheme;
  city: string;
  floors_count: number;
  housing_units_count: number;
  project_start_date: string;
  project_end_date: string;
  project_grace_end_date: string;
  structure_documentation_date: string;
  developer_name: string;
  developer_email: string;
  contractor_name: string;
  contractor_email: string;
  developer_pm_name: string;
  developer_pm_email: string;
  lawyer_name: string;
  lawyer_email: string;
  accompanying_lawyer: string;
  accompanying_lawyer_email: string;
  supervisor_name: string;
  supervisor_email: string;
  architect_name: string;
  architect_email: string;
  site_manager_name: string;
  site_manager_email: string;
};

export function validateProjectCreateForm(
  form: ProjectCreateFormState
):
  | { ok: true; payload: ProjectCreatePayload }
  | { ok: false; message: string } {
  for (const field of REQUIRED_TEXT_FIELDS) {
    if (!form[field].trim()) {
      return {
        ok: false,
        message: "יש למלא את כל שדות החובה בטופס יצירת הפרויקט",
      };
    }
  }

  const floorsRaw = form.floors_count.trim();
  const floors_count = Number(floorsRaw);
  if (!Number.isInteger(floors_count) || floors_count < 1) {
    return {
      ok: false,
      message: "מספר קומות חייב להיות מספר שלם חיובי",
    };
  }

  const housingUnitsRaw = form.housing_units_count.trim();
  const housing_units_count = Number(housingUnitsRaw);
  if (!Number.isInteger(housing_units_count) || housing_units_count < 1) {
    return {
      ok: false,
      message: "מספר יחידות דיור חייב להיות מספר שלם חיובי",
    };
  }

  const emailError = validateProjectEmails(form);
  if (emailError) {
    return {
      ok: false,
      message: emailError,
    };
  }

  return {
    ok: true,
    payload: {
      project_name: form.project_name.trim(),
      scheme: form.scheme as ProjectScheme,
      city: form.city.trim(),
      floors_count,
      housing_units_count,
      project_start_date: form.project_start_date.trim(),
      project_end_date: form.project_end_date.trim(),
      project_grace_end_date: form.project_grace_end_date.trim(),
      structure_documentation_date: form.structure_documentation_date.trim(),
      developer_name: form.developer_name.trim(),
      developer_email: form.developer_email.trim(),
      contractor_name: form.contractor_name.trim(),
      contractor_email: form.contractor_email.trim(),
      developer_pm_name: form.developer_pm_name.trim(),
      developer_pm_email: form.developer_pm_email.trim(),
      lawyer_name: form.lawyer_name.trim(),
      lawyer_email: form.lawyer_email.trim(),
      accompanying_lawyer: form.accompanying_lawyer.trim(),
      accompanying_lawyer_email: form.accompanying_lawyer_email.trim(),
      supervisor_name: form.supervisor_name.trim(),
      supervisor_email: form.supervisor_email.trim(),
      architect_name: form.architect_name.trim(),
      architect_email: form.architect_email.trim(),
      site_manager_name: form.site_manager_name.trim(),
      site_manager_email: form.site_manager_email.trim(),
    },
  };
}
