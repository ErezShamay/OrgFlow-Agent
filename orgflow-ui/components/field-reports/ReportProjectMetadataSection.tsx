"use client";

import {
  PROJECT_SCHEME_OPTIONS,
  projectSchemeLabelHe,
} from "@/lib/field-reports/project-scheme-labels";
import type { ProjectMetadata, ProjectScheme } from "@/lib/field-reports/schema/types";
import {
  UNSPECIFIED_FIELD_LABEL_HE,
} from "@/lib/validation/optional-field-display";
import { validateProjectDates } from "@/lib/validation/project-dates";
import {
  FR_TOUCH_INPUT,
  FR_TOUCH_SELECT,
} from "@/lib/field-reports/touch-input-class";

type ReportProjectMetadataSectionProps = {
  metadata: ProjectMetadata;
  disabled: boolean;
  onChange: (metadata: ProjectMetadata) => void;
};

export default function ReportProjectMetadataSection({
  metadata,
  disabled,
  onChange,
}: ReportProjectMetadataSectionProps) {
  function patch(updates: Partial<ProjectMetadata>) {
    onChange({ ...metadata, ...updates });
  }

  function onSchemeChange(raw: string) {
    if (!raw) {
      patch({ scheme: null, scheme_label_he: null });
      return;
    }

    const scheme = raw as ProjectScheme;
    patch({
      scheme,
      scheme_label_he: projectSchemeLabelHe(scheme),
    });
  }

  const dateValidationError = validateProjectDates(metadata);

  return (
    <section className="space-y-4 rounded-xl border border-zinc-200 p-4 md:p-5">
      <div>
        <h2 className="text-lg font-semibold">פרטי פרויקט</h2>
        <p className="mt-1 text-sm text-zinc-500">
          נטען מפרטי הפרויקט - ניתן לערוך לפני שליחת הדוח.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <label className="block space-y-1 text-sm md:col-span-2">
          <span className="font-medium">סוג פרויקט (תמ״א)</span>
          <select
            className={FR_TOUCH_SELECT}
            value={metadata.scheme ?? ""}
            disabled={disabled}
            onChange={(event) => onSchemeChange(event.target.value)}
          >
            <option value="">- בחר סוג פרויקט -</option>
            {PROJECT_SCHEME_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          {metadata.scheme_label_he ? (
            <span className="block text-xs text-zinc-500">
              {metadata.scheme_label_he}
            </span>
          ) : null}
        </label>

        <DateField
          label="תאריך התחלת פרויקט"
          value={metadata.project_start_date}
          disabled={disabled}
          onChange={(project_start_date) => patch({ project_start_date })}
        />
        <DateField
          label="תאריך סיום פרויקט"
          value={metadata.project_end_date}
          disabled={disabled}
          onChange={(project_end_date) => patch({ project_end_date })}
        />
        <DateField
          label="תאריך גרייס (סיום מורחב)"
          value={metadata.project_grace_end_date}
          disabled={disabled}
          onChange={(project_grace_end_date) =>
            patch({ project_grace_end_date })
          }
        />
        <DateField
          label="תיעוד המבנה מיום"
          value={metadata.structure_documentation_date}
          disabled={disabled}
          onChange={(structure_documentation_date) =>
            patch({ structure_documentation_date })
          }
        />

        <label className="block space-y-1 text-sm">
          <span className="font-medium">מספר יחידות דיור</span>
          <input
            type="number"
            min={0}
            inputMode="numeric"
            className={FR_TOUCH_INPUT}
            value={
              metadata.housing_units_count === null ||
              metadata.housing_units_count === undefined
                ? ""
                : String(metadata.housing_units_count)
            }
            disabled={disabled}
            placeholder={UNSPECIFIED_FIELD_LABEL_HE}
            onChange={(event) => {
              const raw = event.target.value.trim();
              if (!raw) {
                patch({ housing_units_count: null });
                return;
              }
              const parsed = Number.parseInt(raw, 10);
              patch({
                housing_units_count: Number.isFinite(parsed) ? parsed : null,
              });
            }}
          />
        </label>
      </div>

      {dateValidationError ? (
        <p className="text-sm text-red-600" role="alert">
          {dateValidationError}
        </p>
      ) : null}
    </section>
  );
}

function DateField({
  label,
  value,
  disabled,
  onChange,
}: {
  label: string;
  value?: string | null;
  disabled: boolean;
  onChange: (value: string | null) => void;
}) {
  return (
    <label className="block space-y-1 text-sm">
      <span className="font-medium">{label}</span>
      <input
        type="date"
        className={FR_TOUCH_INPUT}
        value={toDateInputValue(value)}
        disabled={disabled}
        onChange={(event) =>
          onChange(event.target.value ? event.target.value : null)
        }
      />
    </label>
  );
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
