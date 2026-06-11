from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from app.config.ai_pricing import resolve_model_pricing
from app.repositories.ai_log_repository import AILogRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.ai_usage import (
    OrganizationAIUsageSummary,
    PlatformAIUsageDashboard,
    PlatformAIUsageTotals,
    PromptUsageSummary,
)
from app.services.ai_runtime_monitoring_service import (
    AIRuntimeMonitoringService,
)

_PRICING_DISCLAIMER = (
    "שימוש בבינה מלאכותית כלול במחיר הבסיסי. "
    "בהתאם לנפח השימוש בפועל, ייתכן עדכון תמחור בעתיד."
)


class AIUsageDashboardService:
    def __init__(
        self,
        *,
        ai_log_repository: AILogRepository | None = None,
        organization_repository: OrganizationRepository | None = None,
        project_repository: ProjectRepository | None = None,
    ) -> None:
        self.ai_log_repository = ai_log_repository or AILogRepository()
        self.organization_repository = (
            organization_repository or OrganizationRepository()
        )
        self.project_repository = project_repository or ProjectRepository()

    def get_platform_dashboard(
        self,
        *,
        period_days: int = 90,
    ) -> PlatformAIUsageDashboard:
        normalized_days = max(period_days, 1)
        since = datetime.now(timezone.utc) - timedelta(days=normalized_days)
        organizations = self.organization_repository.get_all_organizations()
        project_org_map = self._build_project_org_map()
        logs = self.ai_log_repository.list_for_usage_summary(since=since)

        org_stats: dict[str, dict] = {}
        unscoped_stats = self._empty_stats()

        for organization in organizations:
            org_id = str(organization["id"])
            org_stats[org_id] = {
                **self._empty_stats(),
                "organization_name": (
                    organization.get("organization_name")
                    or organization.get("name")
                    or org_id
                ),
                "contact_email": organization.get("contact_email"),
            }

        for log in logs:
            org_id = self._resolve_organization_id(
                log,
                project_org_map,
            )
            stats = org_stats.get(org_id) if org_id else unscoped_stats
            self._accumulate_log(stats, log)

        organization_summaries: list[OrganizationAIUsageSummary] = []

        for org_id, stats in org_stats.items():
            summary = self._build_organization_summary(
                organization_id=org_id,
                stats=stats,
            )
            organization_summaries.append(summary)

        organization_summaries.sort(
            key=lambda item: (
                -item.estimated_cost_usd,
                -item.total_tokens,
                item.organization_name,
            )
        )

        totals = self._build_totals(
            organization_summaries,
            unscoped_stats,
        )

        return PlatformAIUsageDashboard(
            period_days=normalized_days,
            generated_at=datetime.now(timezone.utc),
            pricing_disclaimer=_PRICING_DISCLAIMER,
            totals=totals,
            organizations=organization_summaries,
        )

    def _build_project_org_map(self) -> dict[str, str]:
        mapping: dict[str, str] = {}

        for project in self.project_repository.get_all_projects():
            project_id = str(project.get("id") or "").strip()
            organization_id = str(
                project.get("organization_id") or ""
            ).strip()

            if project_id and organization_id:
                mapping[project_id] = organization_id

        return mapping

    @staticmethod
    def _resolve_organization_id(
        log: dict,
        project_org_map: dict[str, str],
    ) -> str | None:
        organization_id = str(log.get("organization_id") or "").strip()
        if organization_id:
            return organization_id

        project_id = str(log.get("project_id") or "").strip()
        if project_id:
            return project_org_map.get(project_id)

        return None

    @staticmethod
    def _empty_stats() -> dict:
        return {
            "organization_name": "ללא שיוך לקוח",
            "contact_email": None,
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "cache_hits": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "last_activity_at": None,
            "prompts": defaultdict(
                lambda: {
                    "total_calls": 0,
                    "total_tokens": 0,
                    "estimated_cost_usd": 0.0,
                }
            ),
        }

    def _accumulate_log(self, stats: dict, log: dict) -> None:
        prompt_tokens = max(log.get("prompt_tokens") or 0, 0)
        completion_tokens = max(log.get("completion_tokens") or 0, 0)
        total_tokens = prompt_tokens + completion_tokens
        model_name = str(log.get("model_name") or "")
        pricing = resolve_model_pricing(model_name)
        monitoring = AIRuntimeMonitoringService(
            input_cost_per_1k_tokens=pricing.input_cost_per_1k_tokens,
            output_cost_per_1k_tokens=pricing.output_cost_per_1k_tokens,
        )
        estimated_cost = monitoring.calculate_cost_usd(
            prompt_tokens,
            completion_tokens,
        )
        prompt_name = str(log.get("prompt_name") or "ללא שם").strip() or "ללא שם"
        created_at = self._parse_timestamp(log.get("created_at"))

        stats["total_calls"] += 1
        if log.get("success") is True:
            stats["successful_calls"] += 1
        elif log.get("success") is False:
            stats["failed_calls"] += 1

        if log.get("cache_hit") is True:
            stats["cache_hits"] += 1

        stats["total_prompt_tokens"] += prompt_tokens
        stats["total_completion_tokens"] += completion_tokens
        stats["total_tokens"] += total_tokens
        stats["estimated_cost_usd"] = round(
            stats["estimated_cost_usd"] + estimated_cost,
            8,
        )

        if created_at and (
            stats["last_activity_at"] is None
            or created_at > stats["last_activity_at"]
        ):
            stats["last_activity_at"] = created_at

        prompt_stats = stats["prompts"][prompt_name]
        prompt_stats["total_calls"] += 1
        prompt_stats["total_tokens"] += total_tokens
        prompt_stats["estimated_cost_usd"] = round(
            prompt_stats["estimated_cost_usd"] + estimated_cost,
            8,
        )

    def _build_organization_summary(
        self,
        *,
        organization_id: str,
        stats: dict,
    ) -> OrganizationAIUsageSummary:
        usage_by_prompt = [
            PromptUsageSummary(
                prompt_name=prompt_name,
                total_calls=prompt_stats["total_calls"],
                total_tokens=prompt_stats["total_tokens"],
                estimated_cost_usd=prompt_stats["estimated_cost_usd"],
            )
            for prompt_name, prompt_stats in sorted(
                stats["prompts"].items(),
                key=lambda item: (
                    -item[1]["estimated_cost_usd"],
                    -item[1]["total_tokens"],
                    item[0],
                ),
            )
        ]

        return OrganizationAIUsageSummary(
            organization_id=organization_id,
            organization_name=stats["organization_name"],
            contact_email=stats["contact_email"],
            total_calls=stats["total_calls"],
            successful_calls=stats["successful_calls"],
            failed_calls=stats["failed_calls"],
            cache_hits=stats["cache_hits"],
            total_prompt_tokens=stats["total_prompt_tokens"],
            total_completion_tokens=stats["total_completion_tokens"],
            total_tokens=stats["total_tokens"],
            estimated_cost_usd=stats["estimated_cost_usd"],
            last_activity_at=stats["last_activity_at"],
            usage_by_prompt=usage_by_prompt,
        )

    def _build_totals(
        self,
        organization_summaries: list[OrganizationAIUsageSummary],
        unscoped_stats: dict,
    ) -> PlatformAIUsageTotals:
        totals = PlatformAIUsageTotals()

        for summary in organization_summaries:
            totals.total_calls += summary.total_calls
            totals.successful_calls += summary.successful_calls
            totals.failed_calls += summary.failed_calls
            totals.cache_hits += summary.cache_hits
            totals.total_prompt_tokens += summary.total_prompt_tokens
            totals.total_completion_tokens += summary.total_completion_tokens
            totals.total_tokens += summary.total_tokens
            totals.estimated_cost_usd = round(
                totals.estimated_cost_usd + summary.estimated_cost_usd,
                8,
            )
            if summary.total_calls > 0:
                totals.active_organizations += 1

        totals.total_calls += unscoped_stats["total_calls"]
        totals.successful_calls += unscoped_stats["successful_calls"]
        totals.failed_calls += unscoped_stats["failed_calls"]
        totals.cache_hits += unscoped_stats["cache_hits"]
        totals.total_prompt_tokens += unscoped_stats["total_prompt_tokens"]
        totals.total_completion_tokens += (
            unscoped_stats["total_completion_tokens"]
        )
        totals.total_tokens += unscoped_stats["total_tokens"]
        totals.estimated_cost_usd = round(
            totals.estimated_cost_usd + unscoped_stats["estimated_cost_usd"],
            8,
        )

        return totals

    @staticmethod
    def _parse_timestamp(value: object) -> datetime | None:
        if not value:
            return None

        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value

        if isinstance(value, str):
            normalized = value.replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(normalized)
            except ValueError:
                return None
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed

        return None
