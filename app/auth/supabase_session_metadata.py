from __future__ import annotations

import logging

from app.db.supabase_client import supabase

logger = logging.getLogger(__name__)


def sync_active_organization_metadata(
    *,
    user_id: str,
    organization_id: str,
    role: str,
) -> None:
    """
    Store the active tenant on the Supabase Auth user so RLS (Realtime) can read
    auth.jwt()->app_metadata->organization_id. Failures are logged and ignored so
    token exchange never breaks.
    """
    if supabase is None:
        return

    normalized_user_id = user_id.strip()
    normalized_org_id = organization_id.strip()
    normalized_role = role.strip().upper()

    if not normalized_user_id or not normalized_org_id:
        return

    try:
        supabase.auth.admin.update_user_by_id(
            normalized_user_id,
            {
                "app_metadata": {
                    "organization_id": normalized_org_id,
                    "role": normalized_role,
                },
            },
        )
    except Exception:
        logger.warning(
            "Could not sync organization_id to Supabase app_metadata",
            extra={
                "user_id": normalized_user_id,
                "organization_id": normalized_org_id,
            },
            exc_info=True,
        )
