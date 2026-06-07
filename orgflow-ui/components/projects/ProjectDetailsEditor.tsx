"use client";

import { useState } from "react";

import Button from "@/components/ui/Button";
import { apiFetch } from "@/lib/api/client";
import { showToast } from "@/lib/ui/toast";

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
  housing_units_count?: number | null;
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
  housing_units_count: string;
};

function toFormState(project: EditableProjectDetails): FormState {
  return {
    project_name: project.project_name ?? "",
    developer_name: project.developer_name?.trim() ?? "",
    contractor_name: project.contractor_name?.trim() ?? "",
    lawyer_name: project.lawyer_name?.trim() ?? "",
    supervisor_name: project.supervisor_name ?? "",
    supervisor_email: project.supervisor_email?.trim() ?? "",
    developer_pm_name: project.developer_pm_name?.trim() ?? "",
    accompanying_lawyer: project.accompanying_lawyer?.trim() ?? "",
    architect_name: project.architect_name?.trim() ?? "",
    site_manager_name: project.site_manager_name?.trim() ?? "",
    city: project.city?.trim() ?? "",
    housing_units_count:
      project.housing_units_count != null
        ? String(project.housing_units_count)
        : "",
  };
}

function displayValue(value?: string | null) {
  const trimmed = value?.trim();
  return trimmed || "לא צוין";
}

const inputClassName =
  "rounded-2xl border border-zinc-200 bg-transparent p-4 dark:border-zinc-700";

export default function ProjectDetailsEditor({
  project,
  canEdit,
  onSaved,
}: ProjectDetailsEditorProps) {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<FormState>(() => toFormState(project));

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
    ) {
      showToast(
        "יש למלא את כל שדות החובה: שם פרויקט, יזם, קבלן, עו״ד מלווה ומפקח מלווה",
        "error"
      );
      return;
    }

    const housingUnitsRaw = form.housing_units_count.trim();
    let housing_units_count: number | null = null;

    if (housingUnitsRaw) {
      const parsed = Number(housingUnitsRaw);
      if (!Number.isInteger(parsed) || parsed < 0) {
        showToast("מספר יחידות דיור חייב להיות מספר שלם חיובי", "error");
        return;
      }
      housing_units_count = parsed;
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
          supervisor_email: form.supervisor_email.trim() || null,
          developer_pm_name: form.developer_pm_name.trim() || null,
          accompanying_lawyer: form.accompanying_lawyer.trim() || null,
          architect_name: form.architect_name.trim() || null,
          site_manager_name: form.site_manager_name.trim() || null,
          city: form.city.trim() || null,
          housing_units_count,
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
      <div>
        {canEdit ? (
          <div className="mb-6 flex justify-end">
            <Button
              type="button"
              variant="secondary"
              size="md"
              onClick={startEditing}
            >
              עריכת פרטים
            </Button>
          </div>
        ) : null}

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <InfoCard title="שם היזם" value={displayValue(project.developer_name)} />
          <InfoCard title="שם הקבלן" value={displayValue(project.contractor_name)} />
          <InfoCard title="עו״ד מלווה" value={displayValue(project.lawyer_name)} />
          <InfoCard title="מפקח מלווה" value={displayValue(project.supervisor_name)} />
          <InfoCard
            title="אימייל מפקח מלווה"
            value={project.supervisor_email?.trim() || "—"}
          />
          <InfoCard
            title="מנהל פרויקט מטעם יזם"
            value={displayValue(project.developer_pm_name)}
          />
          <InfoCard
            title="עו״ד מלווה (נוסף)"
            value={displayValue(project.accompanying_lawyer)}
          />
          <InfoCard title="אדריכל" value={displayValue(project.architect_name)} />
          <InfoCard
            title="מנהל עבודה"
            value={displayValue(project.site_manager_name)}
          />
          <InfoCard title="עיר" value={displayValue(project.city)} />
          <InfoCard
            title="יחידות דיור"
            value={
              project.housing_units_count != null
                ? String(project.housing_units_count)
                : "לא צוין"
            }
          />
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSave} className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <Field
          label="שם הפרויקט"
          value={form.project_name}
          onChange={(value) =>
            setForm((current) => ({ ...current, project_name: value }))
          }
          required
        />
        <Field
          label="שם היזם"
          value={form.developer_name}
          onChange={(value) =>
            setForm((current) => ({ ...current, developer_name: value }))
          }
          required
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
          label="עו״ד מלווה"
          value={form.lawyer_name}
          onChange={(value) =>
            setForm((current) => ({ ...current, lawyer_name: value }))
          }
          required
        />
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
          label="מנהל פרויקט מטעם יזם"
          value={form.developer_pm_name}
          onChange={(value) =>
            setForm((current) => ({ ...current, developer_pm_name: value }))
          }
        />
        <Field
          label="עו״ד מלווה (נוסף)"
          value={form.accompanying_lawyer}
          onChange={(value) =>
            setForm((current) => ({ ...current, accompanying_lawyer: value }))
          }
        />
        <Field
          label="אדריכל"
          value={form.architect_name}
          onChange={(value) =>
            setForm((current) => ({ ...current, architect_name: value }))
          }
        />
        <Field
          label="מנהל עבודה"
          value={form.site_manager_name}
          onChange={(value) =>
            setForm((current) => ({ ...current, site_manager_name: value }))
          }
        />
        <Field
          label="עיר"
          value={form.city}
          onChange={(value) =>
            setForm((current) => ({ ...current, city: value }))
          }
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
      </div>

      <div className="flex flex-wrap gap-3">
        <Button
          type="submit"
          variant="primary"
          size="lg"
          disabled={saving}
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
};

function Field({
  label,
  value,
  onChange,
  required,
  type = "text",
  min,
}: FieldProps) {
  return (
    <label className="block space-y-2">
      <span className="text-sm font-medium text-zinc-600 dark:text-zinc-300">
        {label}
      </span>
      <input
        className={inputClassName}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required={required}
        type={type}
        min={min}
      />
    </label>
  );
}
