from __future__ import annotations

from uuid import uuid4


class DatabaseSeedService:
    def generate_organization_seed(self, *, name: str = "Demo Org") -> dict:
        org_id = str(uuid4())
        return {
            "organizations": [{
                "id": org_id,
                "name": name,
            }],
            "profiles": [{
                "id": str(uuid4()),
                "organization_id": org_id,
                "email": "admin@demo.org",
                "role": "ADMIN",
            }],
        }

    def generate_project_seed(
        self,
        *,
        organization_id: str,
        project_count: int = 2,
    ) -> dict:
        projects = []
        for index in range(project_count):
            projects.append({
                "id": str(uuid4()),
                "organization_id": organization_id,
                "project_name": f"Demo Project {index + 1}",
                "status": "ACTIVE",
            })
        return {"projects": projects}

    def generate_full_demo(self) -> dict:
        org_seed = self.generate_organization_seed()
        org_id = org_seed["organizations"][0]["id"]
        project_seed = self.generate_project_seed(organization_id=org_id)
        return {
            **org_seed,
            **project_seed,
            "seed_type": "FULL_DEMO",
            "entity_count": (
                len(org_seed["organizations"])
                + len(org_seed["profiles"])
                + len(project_seed["projects"])
            ),
        }

    def list_seed_scripts(self) -> dict:
        return {
            "scripts": [
                {
                    "name": "organization",
                    "description": "Seed a demo organization and admin profile",
                },
                {
                    "name": "projects",
                    "description": "Seed demo projects for an organization",
                },
                {
                    "name": "full_demo",
                    "description": "Seed organization, profile, and projects",
                },
            ],
        }
