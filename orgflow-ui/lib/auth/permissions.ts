export function isAdmin(
  role?: string | null
) {

  return (
    role === "ADMIN"
  );
}

export function isManager(
  role?: string | null
) {

  return [
    "ADMIN",
    "MANAGER",
  ].includes(
    role || ""
  );
}

export function canManageActions(
  role?: string | null
) {

  return [
    "ADMIN",
    "MANAGER",
  ].includes(
    role || ""
  );
}

export function canEscalateActions(
  role?: string | null
) {

  return [
    "ADMIN",
    "MANAGER",
  ].includes(
    role || ""
  );
}

export function canReviewAI(
  role?: string | null
) {

  return [
    "ADMIN",
    "MANAGER",
  ].includes(
    role || ""
  );
}