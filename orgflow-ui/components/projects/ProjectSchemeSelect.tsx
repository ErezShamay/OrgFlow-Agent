import {
  PROJECT_SCHEME_OPTIONS,
  projectSchemeLabelHe,
} from "@/lib/field-reports/project-scheme-labels";
import type { ProjectScheme } from "@/lib/field-reports/schema/types";

type ProjectSchemeSelectProps = {
  value: ProjectScheme | "";
  onChange: (value: ProjectScheme) => void;
  required?: boolean;
  className?: string;
  id?: string;
};

const selectClassName =
  "w-full rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-base dark:border-zinc-700 dark:bg-zinc-900/50";

export function projectSchemeDisplayLabel(
  scheme?: string | null
): string | null {
  if (!scheme) {
    return null;
  }

  if (
    PROJECT_SCHEME_OPTIONS.some((option) => option.value === scheme)
  ) {
    return projectSchemeLabelHe(scheme as ProjectScheme);
  }

  return scheme;
}

export default function ProjectSchemeSelect({
  value,
  onChange,
  required = false,
  className,
  id = "project-scheme",
}: ProjectSchemeSelectProps) {
  return (
    <select
      id={id}
      className={className ?? selectClassName}
      value={value}
      onChange={(event) => onChange(event.target.value as ProjectScheme)}
      required={required}
    >
      <option value="" disabled>
        בחר סוג פרויקט
      </option>
      {PROJECT_SCHEME_OPTIONS.map((option) => (
        <option key={option.value} value={option.value}>
          {projectSchemeLabelHe(option.value)}
        </option>
      ))}
    </select>
  );
}
