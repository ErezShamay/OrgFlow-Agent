from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

IMAGE_DEFINITIONS = [
    {
        "name": "orgflow-api",
        "dockerfile": "Dockerfile",
        "context": ".",
        "port": 8000,
        "base_image": "python:3.12-slim",
        "healthcheck_path": "/health",
    },
    {
        "name": "orgflow-ui",
        "dockerfile": "orgflow-ui/Dockerfile",
        "context": "orgflow-ui",
        "port": 3000,
        "base_image": "node:20-alpine",
        "healthcheck_path": "/",
    },
]


class DockerizationService:
    def list_images(self) -> dict:
        images = []
        for definition in IMAGE_DEFINITIONS:
            dockerfile_path = PROJECT_ROOT / definition["dockerfile"]
            images.append({
                **definition,
                "exists": dockerfile_path.is_file(),
                "path": str(dockerfile_path.relative_to(PROJECT_ROOT)),
            })
        return {
            "images": images,
            "total": len(images),
            "all_present": all(item["exists"] for item in images),
        }

    def validate_dockerfiles(self) -> dict:
        images = self.list_images()["images"]
        missing = [item["name"] for item in images if not item["exists"]]
        return {
            "valid": len(missing) == 0,
            "missing": missing,
            "checked": len(images),
        }

    def get_build_instructions(self, image_name: str = "orgflow-api") -> dict:
        definition = next(
            (item for item in IMAGE_DEFINITIONS if item["name"] == image_name),
            None,
        )
        if definition is None:
            return {"found": False, "image_name": image_name}

        tag = f"{image_name}:latest"
        return {
            "found": True,
            "image_name": image_name,
            "build_command": (
                f"docker build -f {definition['dockerfile']} "
                f"-t {tag} {definition['context']}"
            ),
            "run_command": (
                f"docker run -p {definition['port']}:{definition['port']} {tag}"
            ),
            "dockerfile": definition["dockerfile"],
        }
