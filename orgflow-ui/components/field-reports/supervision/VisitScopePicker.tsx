"use client";

import SupervisionOptionPicker from "@/components/field-reports/supervision/SupervisionOptionPicker";
import type { VisitScope } from "@/lib/field-reports/schema/types";
import { VISIT_SCOPES } from "@/lib/field-reports/schema/types";
import { visitScopeLabelHe } from "@/lib/field-reports/supervision-stage-labels";

const SCOPE_DESCRIPTIONS: Partial<Record<VisitScope, string>> = {
  APARTMENT: "ביקור בדירה אחת",
  PUBLIC_AREA: "ביקור באזור ציבורי אחד (לובי, חניון...)",
};

type VisitScopePickerProps = {
  value: VisitScope | null;
  onChange: (value: VisitScope) => void;
};

export default function VisitScopePicker({
  value,
  onChange,
}: VisitScopePickerProps) {
  return (
    <SupervisionOptionPicker
      label="סוג ביקור"
      value={value}
      onChange={onChange}
      options={VISIT_SCOPES.map((scope) => ({
        value: scope,
        label_he: visitScopeLabelHe(scope),
        description_he: SCOPE_DESCRIPTIONS[scope],
      }))}
    />
  );
}
