from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = PROJECT_ROOT / ".github/workflows"

EXPECTED_WORKFLOWS = [
    {
        "name": "ci",
        "file": "ci.yml",
        "description": "Lint, test, build, and deploy pipeline",
    },
]


class GitHubActionsService:
    def list_workflows(self) -> dict:
        workflows = []
        for expected in EXPECTED_WORKFLOWS:
            path = WORKFLOWS_DIR / expected["file"]
            workflows.append({
                **expected,
                "path": str(path.relative_to(PROJECT_ROOT)),
                "exists": path.is_file(),
            })
        return {
            "workflows": workflows,
            "total": len(workflows),
            "all_present": all(w["exists"] for w in workflows),
        }

    def validate_workflows(self) -> dict:
        workflows = self.list_workflows()["workflows"]
        missing = [w["name"] for w in workflows if not w["exists"]]
        return {
            "valid": len(missing) == 0,
            "missing": missing,
            "checked": len(workflows),
        }

    def get_workflow_summary(self, name: str = "ci") -> dict:
        workflow = next(
            (w for w in EXPECTED_WORKFLOWS if w["name"] == name),
            None,
        )
        if workflow is None:
            return {"found": False, "name": name}

        path = WORKFLOWS_DIR / workflow["file"]
        triggers = []
        if path.is_file():
            content = path.read_text(encoding="utf-8")
            if "push:" in content:
                triggers.append("push")
            if "pull_request:" in content:
                triggers.append("pull_request")

        return {
            "found": True,
            "name": name,
            "file": workflow["file"],
            "description": workflow["description"],
            "triggers": triggers,
            "exists": path.is_file(),
        }
