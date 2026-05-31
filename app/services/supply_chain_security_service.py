from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SUPPLY_CHAIN_CONTROLS = [
    {
        "id": "LOCK_FILES",
        "description": "Pinned dependency lock files committed",
        "paths": ["constraints.txt", "orgflow-ui/package-lock.json"],
    },
    {
        "id": "CI_VERIFICATION",
        "description": "CI validates builds from locked dependencies",
        "paths": [".github/workflows/ci.yml"],
    },
    {
        "id": "DOCKER_PINNED_BASE",
        "description": "Docker base images use explicit tags",
        "paths": ["Dockerfile", "orgflow-ui/Dockerfile"],
    },
]


class SupplyChainSecurityService:
    def get_controls(self) -> dict:
        return {
            "controls": SUPPLY_CHAIN_CONTROLS,
            "total": len(SUPPLY_CHAIN_CONTROLS),
        }

    def validate_controls(self) -> dict:
        results = []
        for control in SUPPLY_CHAIN_CONTROLS:
            missing = []
            for relative_path in control["paths"]:
                if not (PROJECT_ROOT / relative_path).is_file():
                    missing.append(relative_path)
            results.append({
                "id": control["id"],
                "passed": len(missing) == 0,
                "missing": missing,
            })

        return {
            "valid": all(item["passed"] for item in results),
            "controls": results,
            "checked": len(results),
        }

    def get_sbom_status(self) -> dict:
        return {
            "sbom_generated": False,
            "format": "CycloneDX",
            "recommended_action": "Generate SBOM in CI release pipeline",
        }
