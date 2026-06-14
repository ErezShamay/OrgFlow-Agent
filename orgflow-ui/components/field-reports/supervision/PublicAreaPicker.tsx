"use client";

import SupervisionOptionPicker from "@/components/field-reports/supervision/SupervisionOptionPicker";
import type { PublicAreaId } from "@/lib/field-reports/schema/types";
import { PUBLIC_AREA_DEFINITIONS } from "@/lib/field-reports/schema/types";

type PublicAreaPickerProps = {
  value: PublicAreaId | null;
  onChange: (value: PublicAreaId) => void;
};

export default function PublicAreaPicker({
  value,
  onChange,
}: PublicAreaPickerProps) {
  return (
    <SupervisionOptionPicker
      label="אזור ציבורי"
      value={value}
      onChange={onChange}
      options={PUBLIC_AREA_DEFINITIONS.map((area) => ({
        value: area.id,
        label_he: area.label_he,
      }))}
    />
  );
}
