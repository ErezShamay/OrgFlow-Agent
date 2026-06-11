import { STAKEHOLDER_ROLES, type StakeholderRole } from "./schema/types";

/** תוויות עברית לתפקידי בעלי עניין - dropdown ב-UI (FR-1.3). */
export const STAKEHOLDER_ROLE_LABELS_HE: Record<StakeholderRole, string> = {
  developer: "יזם",
  project_manager: "מנהל פרויקט מטעם יזם",
  site_manager: "מנהל עבודה",
  contractor: "קבלן מבצע",
  lawyer_tenants: "עו״ד ב״כ דיירים",
  lawyer_accompanying: "עו״ד מלווה",
  architect: "אדריכל הפרויקט",
};

/** אפשרויות תפקיד ל-select - סדר קבוע לפי STAKEHOLDER_ROLES. */
export const STAKEHOLDER_ROLE_OPTIONS: ReadonlyArray<{
  value: StakeholderRole;
  label: string;
}> = STAKEHOLDER_ROLES.map((role) => ({
  value: role,
  label: STAKEHOLDER_ROLE_LABELS_HE[role],
}));

export function stakeholderRoleLabelHe(role: StakeholderRole): string {
  return STAKEHOLDER_ROLE_LABELS_HE[role];
}
