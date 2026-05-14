import json
from pathlib import Path


class ReportTool:
    def __init__(self):
        self.reports_file = Path(__file__).resolve().parent.parent / "data" / "reports.json"

    def get_weekly_reports(self):
        reports = self._load_reports()

        return [
            report for report in reports
            if report.get("report_type") == "WEEKLY"
        ]

    def find_missing_reports(self, active_projects, weekly_reports):
        reported_project_ids = {
            report["project_id"] for report in weekly_reports
        }

        missing_projects = [
            project for project in active_projects
            if project["project_id"] not in reported_project_ids
        ]

        return missing_projects

    def get_latest_report_by_project_id(self, project_id: str):
        reports = self._load_reports()

        project_reports = [
            report for report in reports
            if report["project_id"] == project_id
        ]

        if not project_reports:
            return None

        return project_reports[-1]

    def _load_reports(self):
        with open(self.reports_file, "r", encoding="utf-8") as file:
            return json.load(file)