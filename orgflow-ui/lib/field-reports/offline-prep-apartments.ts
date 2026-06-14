import type { ProjectApartment } from "@/lib/apartments/types";
import type { OfflinePrepBundle } from "@/lib/field-reports/offline-store-types";

function normalizeProjectApartment(value: unknown): ProjectApartment | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const raw = value as Record<string, unknown>;
  const id = String(raw.id ?? "").trim();
  const organizationId = String(raw.organization_id ?? "").trim();
  const projectId = String(raw.project_id ?? "").trim();
  const apartmentNumber = String(raw.apartment_number ?? "").trim();
  const groupKey = String(raw.group_key ?? "").trim();
  const ownerName = String(raw.owner_name ?? "").trim();
  const inviteStatus = String(raw.invite_status ?? "none").trim();

  if (!id || !organizationId || !projectId || !apartmentNumber) {
    return null;
  }

  return {
    id,
    organization_id: organizationId,
    project_id: projectId,
    apartment_number: apartmentNumber,
    group_key: groupKey || `apartment:${apartmentNumber}`,
    owner_name: ownerName,
    phone: typeof raw.phone === "string" ? raw.phone : null,
    email: typeof raw.email === "string" ? raw.email : null,
    building: typeof raw.building === "string" ? raw.building : null,
    entrance: typeof raw.entrance === "string" ? raw.entrance : null,
    resident_profile_id:
      typeof raw.resident_profile_id === "string"
        ? raw.resident_profile_id
        : null,
    invite_status:
      inviteStatus === "pending" || inviteStatus === "active"
        ? inviteStatus
        : "none",
    created_at: typeof raw.created_at === "string" ? raw.created_at : null,
    updated_at: typeof raw.updated_at === "string" ? raw.updated_at : null,
  };
}

/** דירות לפרויקט מתוך חבילת offline prep (§12.1). */
export function listApartmentsFromOfflineBundle(
  bundle: OfflinePrepBundle | null | undefined,
  projectId: string
): ProjectApartment[] {
  if (!bundle?.apartments_by_project || !projectId) {
    return [];
  }

  const rows = bundle.apartments_by_project[projectId];
  if (!Array.isArray(rows)) {
    return [];
  }

  return rows
    .map((row) => normalizeProjectApartment(row))
    .filter((row): row is ProjectApartment => row !== null);
}
