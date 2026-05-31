class PortfolioHeatmapService:
    HEALTH_BANDS = (
        ("CRITICAL", 0, 49),
        ("WARNING", 50, 79),
        ("HEALTHY", 80, 100),
    )

    RISK_BANDS = (
        ("LOW", 0, 39),
        ("MEDIUM", 40, 69),
        ("HIGH", 70, 100),
    )

    def build_heatmap(self, portfolio_summary: dict) -> dict:
        projects = portfolio_summary.get("projects", [])
        cells = []

        for health_label, health_min, health_max in self.HEALTH_BANDS:
            for risk_label, risk_min, risk_max in self.RISK_BANDS:
                matched = [
                    project
                    for project in projects
                    if (
                        health_min
                        <= project["health"]["score"]
                        <= health_max
                        and risk_min
                        <= project["prediction"]["risk_score"]
                        <= risk_max
                    )
                ]
                cells.append({
                    "health_band": health_label,
                    "risk_band": risk_label,
                    "project_count": len(matched),
                    "projects": [
                        {
                            "project_id": project["project_id"],
                            "project_name": project["project_name"],
                        }
                        for project in matched
                    ],
                })

        return {
            "cells": cells,
            "dimensions": {
                "health_bands": [band[0] for band in self.HEALTH_BANDS],
                "risk_bands": [band[0] for band in self.RISK_BANDS],
            },
            "hottest_cell": self._hottest_cell(cells),
        }

    def _hottest_cell(self, cells: list[dict]) -> dict | None:
        if not cells:
            return None
        return max(cells, key=lambda cell: cell["project_count"])
