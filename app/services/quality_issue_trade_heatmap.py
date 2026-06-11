"""Trade heatmap aggregation - roadmap 6.1."""

from __future__ import annotations

from typing import Any

from app.schemas.quality_issue import (
    QualityIssueSeverity,
    QualityTradeHeatmapCell,
)

UNKNOWN_TRADE_LABEL = "ללא מלאכה"

_SEVERITY_COUNT_FIELDS: dict[QualityIssueSeverity, str] = {
    QualityIssueSeverity.CRITICAL: "open_critical",
    QualityIssueSeverity.HIGH: "open_high",
    QualityIssueSeverity.MEDIUM: "open_medium",
    QualityIssueSeverity.LOW: "open_low",
}


def normalize_trade_label(trade: str | None) -> str:
    normalized = (trade or "").strip()
    return normalized or UNKNOWN_TRADE_LABEL


def _empty_trade_bucket() -> dict[str, int]:
    return {
        "open_total": 0,
        "open_critical": 0,
        "open_high": 0,
        "open_medium": 0,
        "open_low": 0,
    }


def aggregate_open_issues_by_trade(
    open_issues: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    """Group open issues by trade with per-severity counts."""
    per_trade: dict[str, dict[str, int]] = {}

    for issue in open_issues:
        trade = normalize_trade_label(issue.get("trade"))
        bucket = per_trade.setdefault(trade, _empty_trade_bucket())
        bucket["open_total"] += 1

        severity_raw = str(issue.get("severity") or "")
        try:
            severity = QualityIssueSeverity(severity_raw)
        except ValueError:
            continue

        field = _SEVERITY_COUNT_FIELDS.get(severity)
        if field:
            bucket[field] += 1

    return per_trade


def build_trade_heatmap_cells(
    open_issues: list[dict[str, Any]],
) -> list[QualityTradeHeatmapCell]:
    """Build heatmap rows sorted by open_total descending."""
    per_trade = aggregate_open_issues_by_trade(open_issues)

    cells = [
        QualityTradeHeatmapCell(trade=trade, **counts)
        for trade, counts in per_trade.items()
    ]
    cells.sort(
        key=lambda cell: (-cell.open_total, cell.trade),
    )
    return cells
