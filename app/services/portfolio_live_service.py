"""R1 — SSE / polling live portfolio updates."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from app.services.quality_issue_service import QualityIssueService

PORTFOLIO_LIVE_INTERVAL_SECONDS = 30
PORTFOLIO_LIVE_SSE_EVENT = "portfolio.snapshot"


class PortfolioLiveService:
    def __init__(
        self,
        quality_issue_service: QualityIssueService | None = None,
    ) -> None:
        self.quality_issue_service = (
            quality_issue_service or QualityIssueService()
        )

    async def stream_events(
        self,
        *,
        organization_id: str,
        actor_role: str | None,
        actor_user_id: str | None = None,
    ) -> AsyncIterator[str]:
        while True:
            snapshot = self.quality_issue_service.get_portfolio_live_snapshot(
                organization_id=organization_id,
                actor_role=actor_role,
                actor_user_id=actor_user_id,
            )
            payload = json.dumps(
                snapshot.model_dump(mode="json"),
                ensure_ascii=False,
            )
            yield (
                f"event: {PORTFOLIO_LIVE_SSE_EVENT}\n"
                f"data: {payload}\n\n"
            )
            await asyncio.sleep(PORTFOLIO_LIVE_INTERVAL_SECONDS)
