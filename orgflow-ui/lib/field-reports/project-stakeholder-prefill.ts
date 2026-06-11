import { stakeholderRoleLabelHe } from "./stakeholder-role-labels";
import { STAKEHOLDER_ROLES } from "./schema/types";
import type { Stakeholder, StakeholderRole } from "./schema/types";

/** שדות stakeholder בישות פרויקט - לטעינה מ-workspace. */
export type ProjectStakeholderSource = {
  developer_name?: string | null;
  developer_pm_name?: string | null;
  contractor_name?: string | null;
  lawyer_name?: string | null;
  accompanying_lawyer?: string | null;
  architect_name?: string | null;
  site_manager_name?: string | null;
};

const PROJECT_FIELD_BY_ROLE: ReadonlyArray<{
  role: StakeholderRole;
  pick: (project: ProjectStakeholderSource) => string | null | undefined;
}> = [
  { role: "developer", pick: (p) => p.developer_name },
  {
    role: "project_manager",
    pick: (p) => p.developer_pm_name ?? p.contractor_name,
  },
  { role: "site_manager", pick: (p) => p.site_manager_name },
  { role: "contractor", pick: (p) => p.contractor_name },
  { role: "lawyer_tenants", pick: (p) => p.lawyer_name },
  { role: "lawyer_accompanying", pick: (p) => p.accompanying_lawyer },
  { role: "architect", pick: (p) => p.architect_name },
];

/** בונה רשימת stakeholders משדות פרויקט (רק שמות לא ריקים). */
export function stakeholdersFromProject(
  project: ProjectStakeholderSource
): Stakeholder[] {
  const result: Stakeholder[] = [];

  for (const { role, pick } of PROJECT_FIELD_BY_ROLE) {
    const name = pick(project)?.trim();
    if (!name) {
      continue;
    }

    result.push({
      id: `prefill-${role}`,
      role,
      name,
      label_he: stakeholderRoleLabelHe(role),
    });
  }

  return result;
}

/**
 * ממזג prefill לתוך רשימה קיימת - לא דורס שם שכבר מולא בדוח.
 */
export function mergeStakeholderPrefill(
  existing: Stakeholder[],
  prefill: Stakeholder[]
): Stakeholder[] {
  const byRole = new Map<StakeholderRole, Stakeholder>();

  for (const stakeholder of existing) {
    byRole.set(stakeholder.role, stakeholder);
  }

  for (const stakeholder of prefill) {
    const current = byRole.get(stakeholder.role);
    if (current?.name?.trim()) {
      continue;
    }
    byRole.set(stakeholder.role, {
      ...stakeholder,
      id: current?.id ?? stakeholder.id,
    });
  }

  return STAKEHOLDER_ROLES.filter((role) => byRole.has(role)).map(
    (role) => byRole.get(role)!
  );
}
