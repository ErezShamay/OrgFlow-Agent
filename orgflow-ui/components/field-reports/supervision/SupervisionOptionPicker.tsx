"use client";

import { FR_TOUCH_LIST_BUTTON } from "@/lib/field-reports/touch-input-class";

type SupervisionOptionPickerProps<T extends string> = {
  label: string;
  options: ReadonlyArray<{ value: T; label_he: string; description_he?: string }>;
  value: T | null;
  onChange: (value: T) => void;
};

export default function SupervisionOptionPicker<T extends string>({
  label,
  options,
  value,
  onChange,
}: SupervisionOptionPickerProps<T>) {
  return (
    <fieldset className="space-y-2">
      <legend className="text-sm font-medium">{label}</legend>
      <div className="space-y-2">
        {options.map((option) => {
          const selected = value === option.value;

          return (
            <button
              key={option.value}
              type="button"
              className={`${FR_TOUCH_LIST_BUTTON} ${
                selected
                  ? "border-brand bg-brand/5 text-brand dark:border-brand-light dark:text-brand-light"
                  : "border-zinc-200 bg-white hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-950 dark:hover:bg-zinc-900"
              }`}
              aria-pressed={selected}
              onClick={() => onChange(option.value)}
            >
              <span className="block font-medium">{option.label_he}</span>
              {option.description_he ? (
                <span className="mt-0.5 block text-sm text-zinc-500 dark:text-zinc-400">
                  {option.description_he}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
