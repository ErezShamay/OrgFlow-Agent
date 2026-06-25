"use client";

import { useMemo, useState } from "react";

import Button from "@/components/ui/Button";
import { apiFetch } from "@/lib/api/client";
import {
  mergeStakeholderPrefill,
  stakeholdersFromProject,
  type ProjectStakeholderSource,
} from "@/lib/field-reports/project-stakeholder-prefill";
import {
  STAKEHOLDER_ROLE_OPTIONS,
  stakeholderRoleLabelHe,
} from "@/lib/field-reports/stakeholder-role-labels";
import {
  normalizeOptionalTextInput,
  optionalTextForSave,
  UNSPECIFIED_FIELD_LABEL_HE,
} from "@/lib/validation/optional-field-display";
import type { Stakeholder, StakeholderRole, SupplierRow } from "@/lib/field-reports/schema/types";
import { STAKEHOLDER_ROLES } from "@/lib/field-reports/schema/types";
import {
  FR_TOUCH_BUTTON,
  FR_TOUCH_INPUT,
  FR_TOUCH_SELECT,
} from "@/lib/field-reports/touch-input-class";

type ReportStakeholdersSectionProps = {
  stakeholders: Stakeholder[];
  mainSuppliers: SupplierRow[];
  disabled: boolean;
  projectId?: string | null;
  onChange: (update: {
    stakeholders: Stakeholder[];
    main_suppliers: SupplierRow[];
  }) => void;
};

function newStakeholderId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `stakeholder-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function newSupplierId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return `supplier-${crypto.randomUUID()}`;
  }
  return `supplier-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export default function ReportStakeholdersSection({
  stakeholders,
  mainSuppliers,
  disabled,
  projectId,
  onChange,
}: ReportStakeholdersSectionProps) {
  const [suppliersOpen, setSuppliersOpen] = useState(
    () => mainSuppliers.length > 0
  );
  const [prefillLoading, setPrefillLoading] = useState(false);
  const [prefillError, setPrefillError] = useState("");

  const usedRoles = useMemo(
    () => new Set(stakeholders.map((item) => item.role)),
    [stakeholders]
  );

  const availableRoles = useMemo(
    () => STAKEHOLDER_ROLES.filter((role) => !usedRoles.has(role)),
    [usedRoles]
  );

  function emit(
    nextStakeholders: Stakeholder[],
    nextSuppliers: SupplierRow[] = mainSuppliers
  ) {
    onChange({
      stakeholders: nextStakeholders,
      main_suppliers: nextSuppliers,
    });
  }

  function updateStakeholder(
    id: string,
    patch: Partial<Pick<Stakeholder, "role" | "name" | "label_he">>
  ) {
    emit(
      stakeholders.map((item) =>
        item.id === id ? { ...item, ...patch } : item
      )
    );
  }

  function removeStakeholder(id: string) {
    emit(stakeholders.filter((item) => item.id !== id));
  }

  function addStakeholder(role?: StakeholderRole) {
    const nextRole = role ?? availableRoles[0];
    if (!nextRole) {
      return;
    }

    emit([
      ...stakeholders,
      {
        id: newStakeholderId(),
        role: nextRole,
        name: "",
        label_he: stakeholderRoleLabelHe(nextRole),
      },
    ]);
  }

  function updateSupplier(
    id: string,
    patch: Partial<Pick<SupplierRow, "category_he" | "vendor_name">>
  ) {
    emit(
      stakeholders,
      mainSuppliers.map((item) =>
        item.id === id ? { ...item, ...patch } : item
      )
    );
  }

  function addSupplier() {
    setSuppliersOpen(true);
    emit(stakeholders, [
      ...mainSuppliers,
      {
        id: newSupplierId(),
        category_he: "",
        vendor_name: "",
      },
    ]);
  }

  function removeSupplier(id: string) {
    emit(
      stakeholders,
      mainSuppliers.filter((item) => item.id !== id)
    );
  }

  async function prefillFromProject() {
    if (!projectId || disabled) {
      return;
    }

    try {
      setPrefillLoading(true);
      setPrefillError("");

      const response = await apiFetch(`/projects/${projectId}/workspace`);

      if (!response.ok) {
        throw new Error("טעינת פרטי הפרויקט נכשלה");
      }

      const payload = (await response.json()) as {
        project?: ProjectStakeholderSource;
      };
      const project = payload.project;

      if (!project) {
        throw new Error("לא נמצאו פרטי פרויקט");
      }

      const prefill = stakeholdersFromProject(project);
      if (!prefill.length) {
        setPrefillError("אין שמות בעלי עניין בפרויקט למילוי");
        return;
      }

      emit(mergeStakeholderPrefill(stakeholders, prefill));
    } catch (err: unknown) {
      setPrefillError(
        err instanceof Error ? err.message : "מילוי מפרויקט נכשל"
      );
    } finally {
      setPrefillLoading(false);
    }
  }

  const showEmptyLegacyHint =
    stakeholders.length === 0 && !disabled;

  return (
    <section className="space-y-4 rounded-xl border border-zinc-200 p-4 md:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">בעלי עניין</h2>
          <p className="mt-1 text-sm text-zinc-500">
            נטען אוטומטית מפרטי הפרויקט - ניתן לערוך לפני שליחת הדוח.
          </p>
          {showEmptyLegacyHint ? (
            <p className="mt-2 text-sm text-amber-800 dark:text-amber-200">
              טוען פרטים מהפרויקט… אם לא מולאו, לחץ «רענן מפרויקט».
            </p>
          ) : null}
        </div>
        {projectId && !disabled ? (
          <Button
            type="button"
            variant="secondary"
            size="lg"
            className={FR_TOUCH_BUTTON}
            disabled={prefillLoading}
            onClick={() => void prefillFromProject()}
          >
            {prefillLoading ? "טוען..." : "רענן מפרויקט"}
          </Button>
        ) : null}
      </div>

      {prefillError ? (
        <p className="text-sm text-red-600 dark:text-red-400">{prefillError}</p>
      ) : null}

      <ul className="space-y-3">
        {(stakeholders.length > 0 ? stakeholders : []).map((stakeholder) => (
          <li
            key={stakeholder.id}
            className="grid gap-3 rounded-lg border border-zinc-100 bg-zinc-50/80 p-3 md:grid-cols-[minmax(0,11rem)_1fr_auto] dark:border-zinc-800 dark:bg-zinc-900/40"
          >
            <label className="block space-y-1 text-sm">
              <span className="font-medium">תפקיד</span>
              <select
                className={FR_TOUCH_SELECT}
                value={stakeholder.role}
                disabled={disabled}
                onChange={(event) =>
                  updateStakeholder(stakeholder.id, {
                    role: event.target.value as StakeholderRole,
                    label_he: stakeholderRoleLabelHe(
                      event.target.value as StakeholderRole
                    ),
                  })
                }
              >
                {STAKEHOLDER_ROLE_OPTIONS.map((option) => (
                  <option
                    key={option.value}
                    value={option.value}
                    disabled={
                      option.value !== stakeholder.role &&
                      usedRoles.has(option.value)
                    }
                  >
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="block space-y-1 text-sm">
              <span className="font-medium">שם</span>
              <input
                type="text"
                className={FR_TOUCH_INPUT}
                value={normalizeOptionalTextInput(stakeholder.name)}
                disabled={disabled}
                placeholder={stakeholderRoleLabelHe(stakeholder.role)}
                onChange={(event) =>
                  updateStakeholder(stakeholder.id, {
                    name: optionalTextForSave(event.target.value) ?? "",
                  })
                }
              />
            </label>

            {!disabled ? (
              <div className="flex items-end md:justify-end">
                <Button
                  type="button"
                  variant="ghost"
                  size="lg"
                  className={FR_TOUCH_BUTTON}
                  onClick={() => removeStakeholder(stakeholder.id)}
                >
                  הסר
                </Button>
              </div>
            ) : null}
          </li>
        ))}
      </ul>

      {!disabled && stakeholders.length === 0 ? (
        <p className="text-sm text-zinc-500">
          אין רשומות - הוסף תפקיד או לחץ «מלא מפרויקט».
        </p>
      ) : null}

      {!disabled && availableRoles.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="secondary"
            size="lg"
            className={FR_TOUCH_BUTTON}
            onClick={() => addStakeholder()}
          >
            הוסף בעל עניין
          </Button>
          {availableRoles.length <= 3
            ? availableRoles.map((role) => (
                <Button
                  key={role}
                  type="button"
                  variant="ghost"
                  size="lg"
                  className={FR_TOUCH_BUTTON}
                  onClick={() => addStakeholder(role)}
                >
                  + {stakeholderRoleLabelHe(role)}
                </Button>
              ))
            : null}
        </div>
      ) : null}

      <div className="border-t border-zinc-200 pt-4 dark:border-zinc-800">
        <button
          type="button"
          className="flex w-full items-center justify-between gap-2 text-right text-base font-semibold touch-manipulation"
          disabled={disabled && mainSuppliers.length === 0}
          onClick={() => setSuppliersOpen((open) => !open)}
        >
          <span>ספקים עיקריים ({mainSuppliers.length})</span>
          <span className="text-sm font-normal text-zinc-500">
            {suppliersOpen ? "הסתר" : "הצג"}
          </span>
        </button>

        {suppliersOpen ? (
          <div className="mt-3 space-y-3">
            {mainSuppliers.length === 0 ? (
              <p className="text-sm text-zinc-500">אין ספקים - ניתן להוסיף.</p>
            ) : (
              <ul className="space-y-3">
                {mainSuppliers.map((supplier) => (
                  <li
                    key={supplier.id}
                    className="grid gap-3 md:grid-cols-2"
                  >
                    <label className="block space-y-1 text-sm">
                      <span className="font-medium">קטגוריה</span>
                      <input
                        type="text"
                        className={FR_TOUCH_INPUT}
                        value={normalizeOptionalTextInput(supplier.category_he)}
                        disabled={disabled}
                        placeholder="למשל: אינסטלציה"
                        onChange={(event) =>
                          updateSupplier(supplier.id, {
                            category_he:
                              optionalTextForSave(event.target.value) ?? "",
                          })
                        }
                      />
                    </label>
                    <label className="block space-y-1 text-sm">
                      <span className="font-medium">ספק / קבלן</span>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          className={FR_TOUCH_INPUT}
                          value={normalizeOptionalTextInput(supplier.vendor_name)}
                          disabled={disabled}
                          placeholder={UNSPECIFIED_FIELD_LABEL_HE}
                          onChange={(event) =>
                            updateSupplier(supplier.id, {
                              vendor_name:
                                optionalTextForSave(event.target.value) ?? "",
                            })
                          }
                        />
                        {!disabled ? (
                          <Button
                            type="button"
                            variant="ghost"
                            size="lg"
                            className={`shrink-0 ${FR_TOUCH_BUTTON}`}
                            onClick={() => removeSupplier(supplier.id)}
                          >
                            הסר
                          </Button>
                        ) : null}
                      </div>
                    </label>
                  </li>
                ))}
              </ul>
            )}

            {!disabled ? (
              <Button
                type="button"
                variant="secondary"
                size="lg"
                className={FR_TOUCH_BUTTON}
                onClick={addSupplier}
              >
                הוסף ספק
              </Button>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  );
}
