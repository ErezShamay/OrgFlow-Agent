"use client";

import SupervisionOptionPicker from "@/components/field-reports/supervision/SupervisionOptionPicker";
import type { ConstructionStage } from "@/lib/field-reports/schema/types";
import { CONSTRUCTION_STAGES } from "@/lib/field-reports/schema/types";
import { constructionStageLabelHe } from "@/lib/field-reports/supervision-stage-labels";

const STAGE_DESCRIPTIONS: Partial<Record<ConstructionStage, string>> = {
  STRUCTURE: "בדיקות שלד ויסודות",
  FINISHING: "בדיקות גמר דירה / שטחים ציבוריים",
  MIXED: "כל שלבי הבנייה",
};

type ConstructionStagePickerProps = {
  value: ConstructionStage | null;
  onChange: (value: ConstructionStage) => void;
};

export default function ConstructionStagePicker({
  value,
  onChange,
}: ConstructionStagePickerProps) {
  return (
    <SupervisionOptionPicker
      label="שלב בנייה"
      value={value}
      onChange={onChange}
      options={CONSTRUCTION_STAGES.map((stage) => ({
        value: stage,
        label_he: constructionStageLabelHe(stage),
        description_he: STAGE_DESCRIPTIONS[stage],
      }))}
    />
  );
}
