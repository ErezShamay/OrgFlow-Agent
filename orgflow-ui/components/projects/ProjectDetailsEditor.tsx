"use client";

import { useState } from "react";

import ProjectIllustrationUpload from "@/components/projects/ProjectIllustrationUpload";
import ProjectSchemeSelect, {
  projectSchemeDisplayLabel,
} from "@/components/projects/ProjectSchemeSelect";
import Button from "@/components/ui/Button";
import { apiFetch } from "@/lib/api/client";
import type { ProjectScheme } from "@/lib/field-reports/schema/types";
import { PROJECT_SCHEME_OPTIONS } from "@/lib/field-reports/project-scheme-labels";
import { showToast } from "@/lib/ui/toast";
import { validateOptionalProjectEmails } from "@/lib/validation/email";
import {
  displayOptionalText,
  normalizeOptionalTextInput,
  optionalTextForSave,
  UNSPECIFIED_FIELD_LABEL_HE,
} from "@/lib/validation/optional-field-display";
import { validateProjectDates } from "@/lib/validation/project-dates";

export type EditableProjectDetails = {
  id: string;
  project_name: string;
  developer_name?: string | null;
  contractor_name?: string | null;
  lawyer_name?: string | null;
  supervisor_name: string;
  supervisor_email?: string | null;
  developer_pm_name?: string | null;
  accompanying_lawyer?: string | null;
  architect_name?: string | null;
  site_manager_name?: string | null;
  city?: string | null;
  scheme?: string | null;
  housing_units_count?: number | null;
  floors_count?: number | null;
  project_start_date?: string | null;
  project_end_date?: string | null;
  project_grace_end_date?: string | null;
  structure_documentation_date?: string | null;
  illustration_url?: string | null;
  illustration_source_he?: string | null;
  developer_email?: string | null;
  developer_pm_email?: string | null;
  site_manager_email?: string | null;
  contractor_email?: string | null;
  lawyer_email?: string | null;
  accompanying_lawyer_email?: string | null;
  architect_email?: string | null;
};

type ProjectDetailsEditorProps = {
  project: EditableProjectDetails;
  canEdit: boolean;
  onSaved: () => Promise<void> | void;
};

type FormState = {
  project_name: string;
  developer_name: string;
  contractor_name: string;
  lawyer_name: string;
  supervisor_name: string;
  supervisor_email: string;
  developer_pm_name: string;
  accompanying_lawyer: string;
  architect_name: string;
  site_manager_name: string;
  city: string;
  scheme: ProjectScheme | "";
  housing_units_count: string;
  floors_count: string;
  project_start_date: string;
  project_end_date: string;
  project_grace_end_date: string;
  structure_documentation_date: string;
  developer_email: string;
  developer_pm_email: string;
  site_manager_email: string;
  contractor_email: string;
  lawyer_email: string;
  accompanying_lawyer_email: string;
  architect_email: string;
};

function toFormState(project: EditableProjectDetails): FormState {
  return {
    project_name: normalizeOptionalTextInput(project.project_name),
    developer_name: normalizeOptionalTextInput(project.developer_name),
    contractor_name: normalizeOptionalTextInput(project.contractor_name),
    lawyer_name: normalizeOptionalTextInput(project.lawyer_name),
    supervisor_name: normalizeOptionalTextInput(project.supervisor_name),
    supervisor_email: normalizeOptionalTextInput(project.supervisor_email),
    developer_pm_name: normalizeOptionalTextInput(project.developer_pm_name),
    accompanying_lawyer: normalizeOptionalTextInput(project.accompanying_lawyer),
    architect_name: normalizeOptionalTextInput(project.architect_name),
    site_manager_name: normalizeOptionalTextInput(project.site_manager_name),
    city: normalizeOptionalTextInput(project.city),
    scheme:
      PROJECT_SCHEME_OPTIONS.some(
        (option) => option.value === project.scheme
      )
        ? (project.scheme as ProjectScheme)
        : "",
    housing_units_count:
      project.housing_units_count != null
        ? String(project.housing_units_count)
        : "",
    floors_count:
      project.floors_count != null ? String(project.floors_count) : "",
    project_start_date: toDateInputValue(project.project_start_date),
    project_end_date: toDateInputValue(project.project_end_date),
    project_grace_end_date: toDateInputValue(project.project_grace_end_date),
    structure_documentation_date: toDateInputValue(
      project.structure_documentation_date
    ),
    developer_email: normalizeOptionalTextInput(project.developer_email),
    developer_pm_email: normalizeOptionalTextInput(project.developer_pm_email),
    site_manager_email: normalizeOptionalTextInput(project.site_manager_email),
    contractor_email: normalizeOptionalTextInput(project.contractor_email),
    lawyer_email: normalizeOptionalTextInput(project.lawyer_email),
    accompanying_lawyer_email: normalizeOptionalTextInput(
      project.accompanying_lawyer_email
    ),
    architect_email: normalizeOptionalTextInput(project.architect_email),
  };
}

function formatDisplayDate(value?: string | null) {
  const inputValue = toDateInputValue(value);
  if (!inputValue) {
    return UNSPECIFIED_FIELD_LABEL_HE;
  }

  try {
    return new Date(`${inputValue}T00:00:00`).toLocaleDateString("he-IL");
  } catch {
    return inputValue;
  }
}

function toDateInputValue(value?: string | null): string {
  if (!value) {
    return "";
  }

  const trimmed = value.trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
    return trimmed;
  }

  const parsed = new Date(trimmed);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }

  return parsed.toISOString().slice(0, 10);
}

const inputClassName =
  "w-full rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-base dark:border-zinc-700 dark:bg-zinc-900/50";

const sectionClassName =
  "rounded-2xl border border-zinc-200/80 bg-zinc-50/50 p-6 dark:border-zinc-700/80 dark:bg-zinc-900/30";

const sectionGridClassName =
  "grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-3";

export default function ProjectDetailsEditor({
  project,
  canEdit,
  onSaved,
}: ProjectDetailsEditorProps) {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<FormState>(() => toFormState(project));
  const dateValidationError = validateProjectDates({
    project_start_date: form.project_start_date,
    project_end_date: form.project_end_date,
    project_grace_end_date: form.project_grace_end_date,
  });

  function startEditing() {
    setForm(toFormState(project));
    setEditing(true);
  }

  function cancelEditing() {
    setForm(toFormState(project));
    setEditing(false);
  }

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();

    if (
      !form.project_name.trim()
      || !form.developer_name.trim()
      || !form.contractor_name.trim()
      || !form.lawyer_name.trim()
      || !form.supervisor_name.trim()
      || !form.scheme
    ) {
      showToast(
        "יש למלא את כל שדות החובה: שם פרויקט, סוג פרויקט, יזם, קבלן, עו״ד מלווה ומפקח מלווה",
        "error"
      );
      return;
    }

    const housingUnitsRaw = form.housing_units_count.trim();
    let housing_units_count: number | null = null;

    if (housingUnitsRaw) {
      const parsed = Number(housingUnitsRaw);
      if (!Number.isInteger(parsed) || parsed < 1) {
        showToast("מספר יחידות דיור חייב להיות מספר שלם חיובי", "error");
        return;
      }
      housing_units_count = parsed;
    }

    const floorsRaw = form.floors_count.trim();
    let floors_count: number | null = null;

    if (floorsRaw) {
      const parsed = Number(floorsRaw);
      if (!Number.isInteger(parsed) || parsed < 1) {
        showToast("מספר קומות חייב להיות מספר שלם חיובי", "error");
        return;
      }
      floors_count = parsed;
    }

    const emailError = validateOptionalProjectEmails(form);
    if (emailError) {
      showToast(emailError, "error");
      return;
    }

    if (dateValidationError) {
      showToast(dateValidationError, "error");
      return;
    }

    try {
      setSaving(true);

      const response = await apiFetch(`/projects/${project.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          project_name: form.project_name.trim(),
          developer_name: form.developer_name.trim(),
          contractor_name: form.contractor_name.trim(),
          lawyer_name: form.lawyer_name.trim(),
          supervisor_name: form.supervisor_name.trim(),
          supervisor_email: optionalTextForSave(form.supervisor_email),
          developer_pm_name: optionalTextForSave(form.developer_pm_name),
          accompanying_lawyer: optionalTextForSave(form.accompanying_lawyer),
          architect_name: optionalTextForSave(form.architect_name),
          site_manager_name: optionalTextForSave(form.site_manager_name),
          city: optionalTextForSave(form.city),
          scheme: form.scheme,
          housing_units_count,
          floors_count,
          project_start_date: form.project_start_date.trim() || null,
          project_end_date: form.project_end_date.trim() || null,
          project_grace_end_date: form.project_grace_end_date.trim() || null,
          structure_documentation_date:
            form.structure_documentation_date.trim() || null,
          developer_email: optionalTextForSave(form.developer_email),
          developer_pm_email: optionalTextForSave(form.developer_pm_email),
          site_manager_email: optionalTextForSave(form.site_manager_email),
          contractor_email: optionalTextForSave(form.contractor_email),
          lawyer_email: optionalTextForSave(form.lawyer_email),
          accompanying_lawyer_email: optionalTextForSave(
            form.accompanying_lawyer_email
          ),
          architect_email: optionalTextForSave(form.architect_email),
        }),
      });

      if (!response.ok) {
        throw new Error("שמירת פרטי הפרויקט נכשלה");
      }

      showToast("פרטי הפרויקט נשמרו", "success");
      setEditing(false);
      await onSaved();
    } catch {
      showToast("שמירת פרטי הפרויקט נכשלה", "error");
    } finally {
      setSaving(false);
    }
  }

  if (!editing) {
    return (
      <div className="mt-10 border-t border-zinc-200 pt-10 dark:border-zinc-700">
        <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold">פרטי הפרויקט</h2>
            <p className="mt-2 text-sm leading-relaxed text-zinc-500">
              {canEdit
                ? "יזם, קבלן, עורכי דין, מפקח ואנשי קשר — כולל מיילים לשליחת דוחות אוטומטית אחרי Finalize"
                : "צפייה בלבד - לעריכה נדרשת הרשאת מנהל, מפקח או מנהל תפעול"}
            </p>
          </div>

          {canEdit ? (
            <Button
              type="button"
              variant="secondary"
              size="md"
              onClick={startEditing}
            >
              עריכת פרטים
            </Button>
          ) : null}
        </div>

        <div className="space-y-8">
          <ProjectIllustrationUpload
            projectId={project.id}
            illustrationUrl={project.illustration_url}
            illustrationSourceHe={project.illustration_source_he}
            canEdit={canEdit}
            onUploaded={onSaved}
          />

          <DetailsSection title="פרטים כלליים">
            <InfoCard
              title="שם הפרויקט"
              value={displayOptionalText(project.project_name)}
            />
            <InfoCard
              title="סוג פרויקט"
              value={
                projectSchemeDisplayLabel(project.scheme)
                ?? UNSPECIFIED_FIELD_LABEL_HE
              }
            />
            <InfoCard title="עיר" value={displayOptionalText(project.city)} />
            <InfoCard
              title="מספר קומות"
              value={
                project.floors_count != null
                  ? String(project.floors_count)
                  : UNSPECIFIED_FIELD_LABEL_HE
              }
            />
            <InfoCard
              title="יחידות דיור"
              value={
                project.housing_units_count != null
                  ? String(project.housing_units_count)
                  : UNSPECIFIED_FIELD_LABEL_HE
              }
            />
            <InfoCard
              title="תאריך תחילת פרויקט"
              value={formatDisplayDate(project.project_start_date)}
            />
            <InfoCard
              title="תאריך סיום פרויקט"
              value={formatDisplayDate(project.project_end_date)}
            />
            <InfoCard
              title="תאריך סיום תקופת חסד"
              value={formatDisplayDate(project.project_grace_end_date)}
            />
            <InfoCard
              title="תאריך תיעוד מבנה"
              value={formatDisplayDate(project.structure_documentation_date)}
            />
          </DetailsSection>

          <DetailsSection title="יזם וקבלן">
            <InfoCard
              title="שם היזם"
              value={displayOptionalText(project.developer_name)}
            />
            <InfoCard
              title="אימייל יזם"
              value={project.developer_email?.trim() || "-"}
            />
            <InfoCard
              title="שם הקבלן"
              value={displayOptionalText(project.contractor_name)}
            />
            <InfoCard
              title="אימייל קבלן"
              value={project.contractor_email?.trim() || "-"}
            />
            <InfoCard
              title="מנהל פרויקט מטעם יזם"
              value={displayOptionalText(project.developer_pm_name)}
            />
            <InfoCard
              title="אימייל מנהל פרויקט (יזם)"
              value={project.developer_pm_email?.trim() || "-"}
            />
          </DetailsSection>

          <DetailsSection title="ייעוץ משפטי">
            <InfoCard
              title="עו״ד מלווה"
              value={displayOptionalText(project.lawyer_name)}
            />
            <InfoCard
              title="אימייל עו״ד מלווה"
              value={project.lawyer_email?.trim() || "-"}
            />
            <InfoCard
              title="עו״ד מלווה (נוסף)"
              value={displayOptionalText(project.accompanying_lawyer)}
            />
            <InfoCard
              title="אימייל עו״ד מלווה (נוסף)"
              value={project.accompanying_lawyer_email?.trim() || "-"}
            />
          </DetailsSection>

          <DetailsSection title="פיקוח וניהול">
            <InfoCard
              title="מפקח מלווה"
              value={displayOptionalText(project.supervisor_name)}
            />
            <InfoCard
              title="אימייל מפקח מלווה"
              value={project.supervisor_email?.trim() || "-"}
            />
            <InfoCard
              title="אדריכל"
              value={displayOptionalText(project.architect_name)}
            />
            <InfoCard
              title="אימייל אדריכל"
              value={project.architect_email?.trim() || "-"}
            />
            <InfoCard
              title="מנהל עבודה"
              value={displayOptionalText(project.site_manager_name)}
            />
            <InfoCard
              title="אימייל מנהל עבודה"
              value={project.site_manager_email?.trim() || "-"}
            />
          </DetailsSection>
        </div>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSave}
      className="mt-10 border-t border-zinc-200 pt-10 dark:border-zinc-700"
    >
      <div className="mb-8">
        <h2 className="text-2xl font-bold">עריכת פרטי הפרויקט</h2>
        <p className="mt-2 text-sm leading-relaxed text-zinc-500">
          עדכון אנשי קשר ומיילים — נמעני דוחות אוטומטיים אחרי Finalize (בנוסף לדיירים במודול דירות)
        </p>
      </div>

      <div className="space-y-8">
        <ProjectIllustrationUpload
          projectId={project.id}
          illustrationUrl={project.illustration_url}
          illustrationSourceHe={project.illustration_source_he}
          canEdit={canEdit}
          onUploaded={onSaved}
        />

        <DetailsSection title="פרטים כלליים">
          <Field
            label="שם הפרויקט"
            value={form.project_name}
            onChange={(value) =>
              setForm((current) => ({ ...current, project_name: value }))
            }
            required
            className="sm:col-span-2 xl:col-span-3"
          />
          <Field
            label="עיר"
            value={form.city}
            onChange={(value) =>
              setForm((current) => ({ ...current, city: value }))
            }
          />
          <div>
            <label
              htmlFor="edit-project-scheme"
              className="mb-2 block text-sm font-medium text-zinc-600 dark:text-zinc-400"
            >
              סוג פרויקט *
            </label>
            <ProjectSchemeSelect
              id="edit-project-scheme"
              value={form.scheme}
              onChange={(scheme) =>
                setForm((current) => ({ ...current, scheme }))
              }
              required
            />
          </div>
          <Field
            label="מספר קומות"
            value={form.floors_count}
            onChange={(value) =>
              setForm((current) => ({ ...current, floors_count: value }))
            }
            type="number"
            min={1}
          />
          <Field
            label="יחידות דיור"
            value={form.housing_units_count}
            onChange={(value) =>
              setForm((current) => ({ ...current, housing_units_count: value }))
            }
            type="number"
            min={0}
          />
          <Field
            label="תאריך תחילת פרויקט"
            value={form.project_start_date}
            onChange={(value) =>
              setForm((current) => ({ ...current, project_start_date: value }))
            }
            type="date"
          />
          <Field
            label="תאריך סיום פרויקט"
            value={form.project_end_date}
            onChange={(value) =>
              setForm((current) => ({ ...current, project_end_date: value }))
            }
            type="date"
          />
          <Field
            label="תאריך סיום תקופת חסד"
            value={form.project_grace_end_date}
            onChange={(value) =>
              setForm((current) => ({
                ...current,
                project_grace_end_date: value,
              }))
            }
            type="date"
          />
          <Field
            label="תאריך תיעוד מבנה"
            value={form.structure_documentation_date}
            onChange={(value) =>
              setForm((current) => ({
                ...current,
                structure_documentation_date: value,
              }))
            }
            type="date"
          />
          {dateValidationError ? (
            <p
              className="text-sm text-red-600 sm:col-span-2 xl:col-span-3"
              role="alert"
            >
              {dateValidationError}
            </p>
          ) : null}
        </DetailsSection>

        <DetailsSection title="יזם וקבלן">
          <Field
            label="שם היזם"
            value={form.developer_name}
            onChange={(value) =>
              setForm((current) => ({ ...current, developer_name: value }))
            }
            required
          />
          <Field
            label="אימייל יזם"
            value={form.developer_email}
            onChange={(value) =>
              setForm((current) => ({ ...current, developer_email: value }))
            }
            type="email"
          />
          <Field
            label="שם הקבלן"
            value={form.contractor_name}
            onChange={(value) =>
              setForm((current) => ({ ...current, contractor_name: value }))
            }
            required
          />
          <Field
            label="אימייל קבלן"
            value={form.contractor_email}
            onChange={(value) =>
              setForm((current) => ({ ...current, contractor_email: value }))
            }
            type="email"
          />
          <Field
            label="מנהל פרויקט מטעם יזם"
            value={form.developer_pm_name}
            onChange={(value) =>
              setForm((current) => ({ ...current, developer_pm_name: value }))
            }
          />
          <Field
            label="אימייל מנהל פרויקט (יזם)"
            value={form.developer_pm_email}
            onChange={(value) =>
              setForm((current) => ({ ...current, developer_pm_email: value }))
            }
            type="email"
          />
        </DetailsSection>

        <DetailsSection title="ייעוץ משפטי">
          <Field
            label="עו״ד מלווה"
            value={form.lawyer_name}
            onChange={(value) =>
              setForm((current) => ({ ...current, lawyer_name: value }))
            }
            required
          />
          <Field
            label="אימייל עו״ד מלווה"
            value={form.lawyer_email}
            onChange={(value) =>
              setForm((current) => ({ ...current, lawyer_email: value }))
            }
            type="email"
          />
          <Field
            label="עו״ד מלווה (נוסף)"
            value={form.accompanying_lawyer}
            onChange={(value) =>
              setForm((current) => ({ ...current, accompanying_lawyer: value }))
            }
          />
          <Field
            label="אימייל עו״ד מלווה (נוסף)"
            value={form.accompanying_lawyer_email}
            onChange={(value) =>
              setForm((current) => ({
                ...current,
                accompanying_lawyer_email: value,
              }))
            }
            type="email"
          />
        </DetailsSection>

        <DetailsSection title="פיקוח וניהול">
          <Field
            label="מפקח מלווה"
            value={form.supervisor_name}
            onChange={(value) =>
              setForm((current) => ({ ...current, supervisor_name: value }))
            }
            required
          />
          <Field
            label="אימייל מפקח מלווה"
            value={form.supervisor_email}
            onChange={(value) =>
              setForm((current) => ({ ...current, supervisor_email: value }))
            }
            type="email"
          />
          <Field
            label="אדריכל"
            value={form.architect_name}
            onChange={(value) =>
              setForm((current) => ({ ...current, architect_name: value }))
            }
          />
          <Field
            label="אימייל אדריכל"
            value={form.architect_email}
            onChange={(value) =>
              setForm((current) => ({ ...current, architect_email: value }))
            }
            type="email"
          />
          <Field
            label="מנהל עבודה"
            value={form.site_manager_name}
            onChange={(value) =>
              setForm((current) => ({ ...current, site_manager_name: value }))
            }
          />
          <Field
            label="אימייל מנהל עבודה"
            value={form.site_manager_email}
            onChange={(value) =>
              setForm((current) => ({ ...current, site_manager_email: value }))
            }
            type="email"
          />
        </DetailsSection>
      </div>

      <div className="mt-10 flex flex-wrap gap-4 border-t border-zinc-200 pt-8 dark:border-zinc-700">
        <Button
          type="submit"
          variant="primary"
          size="lg"
          disabled={saving || Boolean(dateValidationError)}
        >
          {saving ? "שומר..." : "שמירה"}
        </Button>
        <Button
          type="button"
          variant="secondary"
          size="lg"
          disabled={saving}
          onClick={cancelEditing}
        >
          ביטול
        </Button>
      </div>
    </form>
  );
}

type DetailsSectionProps = {
  title: string;
  children: React.ReactNode;
};

function DetailsSection({
  title,
  children,
}: DetailsSectionProps) {
  return (
    <section className={sectionClassName}>
      <h3 className="mb-6 text-lg font-semibold text-zinc-800 dark:text-zinc-100">
        {title}
      </h3>
      <div className={sectionGridClassName}>
        {children}
      </div>
    </section>
  );
}

type InfoCardProps = {
  title: string;
  value: string;
};

function InfoCard({ title, value }: InfoCardProps) {
  return (
    <div className="of-info-card">
      <p className="of-info-card-label">{title}</p>
      <p className="of-info-card-value">{value}</p>
    </div>
  );
}

type FieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  type?: string;
  min?: number;
  className?: string;
  placeholder?: string;
};

function Field({
  label,
  value,
  onChange,
  required,
  type = "text",
  min,
  className = "",
  placeholder = !required && type !== "date" && type !== "number"
    ? UNSPECIFIED_FIELD_LABEL_HE
    : undefined,
}: FieldProps) {
  return (
    <label className={`block space-y-3 ${className}`}>
      <span className="block text-sm font-medium text-zinc-600 dark:text-zinc-300">
        {label}
        {required ? (
          <span className="ms-1 text-red-500" aria-hidden>
            *
          </span>
        ) : null}
      </span>
      <input
        className={inputClassName}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required={required}
        type={type}
        min={min}
        placeholder={placeholder}
      />
    </label>
  );
}
