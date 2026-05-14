import json
from pathlib import Path
from difflib import get_close_matches


class ProjectTool:
    def __init__(self):
        self.projects_file = Path(__file__).resolve().parent.parent / "data" / "projects.json"

    def get_active_projects(self):
        projects = self._load_projects()

        return [
            project for project in projects
            if project.get("status") == "ACTIVE"
        ]

    def find_project_by_name(self, project_name: str):
        projects = self._load_projects()

        # Exact match
        for project in projects:
            if project["project_name"] == project_name:
                return {
                    "match_status": "EXACT_MATCH",
                    "project": project,
                    "suggestions": []
                }

        # Contains match
        for project in projects:
            if project_name in project["project_name"] or project["project_name"] in project_name:
                return {
                    "match_status": "PARTIAL_MATCH",
                    "project": project,
                    "suggestions": []
                }

        # Fuzzy match
        project_names = [project["project_name"] for project in projects]
        matches = get_close_matches(project_name, project_names, n=3, cutoff=0.7)

        if len(matches) == 1:
            matched_project = next(
                project for project in projects
                if project["project_name"] == matches[0]
            )

            return {
                "match_status": "FUZZY_MATCH",
                "project": matched_project,
                "suggestions": []
            }

        if len(matches) > 1:
            return {
                "match_status": "MULTIPLE_MATCHES",
                "project": None,
                "suggestions": matches
            }

        return {
            "match_status": "NOT_FOUND",
            "project": None,
            "suggestions": []
        }

    def _load_projects(self):
        with open(self.projects_file, "r", encoding="utf-8") as file:
            return json.load(file)