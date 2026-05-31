from __future__ import annotations

PIPELINE_STAGES = [
    {"name": "lint", "jobs": ["backend-lint", "frontend-lint"]},
    {"name": "test", "jobs": ["backend-tests", "frontend-tests"]},
    {"name": "build", "jobs": ["docker-build-api", "docker-build-ui"]},
    {"name": "deploy-staging", "jobs": ["deploy-staging"]},
    {"name": "deploy-production", "jobs": ["deploy-production"], "manual": True},
]


class CicdPipelineService:
    def get_pipeline_definition(self) -> dict:
        return {
            "provider": "github-actions",
            "workflow_file": ".github/workflows/ci.yml",
            "stages": PIPELINE_STAGES,
            "triggers": ["push", "pull_request"],
            "branches": ["main", "develop"],
        }

    def get_stage_status(self) -> dict:
        stages = []
        for stage in PIPELINE_STAGES:
            stages.append({
                **stage,
                "status": "CONFIGURED",
                "last_run": None,
            })
        return {
            "stages": stages,
            "total_stages": len(stages),
            "ready": True,
        }

    def validate_pipeline(self) -> dict:
        from pathlib import Path

        workflow = (
            Path(__file__).resolve().parents[2]
            / ".github/workflows/ci.yml"
        )
        exists = workflow.is_file()
        required_jobs = [
            job
            for stage in PIPELINE_STAGES
            for job in stage["jobs"]
        ]
        jobs_found = []
        if exists:
            content = workflow.read_text(encoding="utf-8")
            jobs_found = [job for job in required_jobs if job in content]
        return {
            "valid": exists and len(jobs_found) >= 4,
            "workflow_exists": exists,
            "jobs_found": jobs_found,
            "expected_jobs": required_jobs,
        }
