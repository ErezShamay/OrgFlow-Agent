from app.repositories.project_repository import (
    ProjectRepository
)
from datetime import datetime, timezone
from uuid import uuid4


class ProjectService:

    def __init__(self):

        self.project_repository = (
            ProjectRepository()
        )
        self.project_comments: dict[str, list[dict]] = {}
        self.project_attachments: dict[str, list[dict]] = {}

    def create_project(
        self,
        project_name: str,
        supervisor_name: str,
        supervisor_email: str | None = None,
        organization_id: str | None = None,
        owner_id: str | None = None,
        tags: list[str] | None = None,
    ):
        normalized_tags = self._normalize_tags(tags)
        return (
            self.project_repository
            .create_project(
                project_name=
                    project_name,

                supervisor_name=
                    supervisor_name,

                supervisor_email=
                    supervisor_email,

                organization_id=
                    organization_id,

                owner_id=
                    owner_id,

                tags=
                    normalized_tags,

                status=
                    "ACTIVE",
            )
        )

    def edit_project(
        self,
        project_id: str,
        *,
        project_name: str | None = None,
        supervisor_name: str | None = None,
        supervisor_email: str | None = None,
    ):
        updates = {
            "project_name": project_name,
            "supervisor_name": supervisor_name,
            "supervisor_email": supervisor_email,
        }
        return self.project_repository.update_project(project_id, updates)

    def archive_project(
        self,
        project_id: str,
    ):
        updates = {
            "status": "ARCHIVED",
        }
        return self.project_repository.update_project(project_id, updates)

    def delete_project(
        self,
        project_id: str,
    ) -> bool:
        return self.project_repository.delete_project(project_id)

    def search_projects(
        self,
        query: str,
    ):
        if not query.strip():
            return []
        return self.project_repository.search_projects(query=query.strip())

    def filter_projects(
        self,
        *,
        status: str | None = None,
        owner_id: str | None = None,
        tag: str | None = None,
    ):
        normalized_status = status.upper() if status else None
        normalized_tag = tag.strip().lower() if tag else None
        return self.project_repository.filter_projects(
            status=normalized_status,
            owner_id=owner_id,
            tag=normalized_tag,
        )

    def update_project_tags(
        self,
        project_id: str,
        tags: list[str],
    ):
        normalized_tags = self._normalize_tags(tags)
        return self.project_repository.update_project(
            project_id,
            {"tags": normalized_tags},
        )

    def set_project_owner(
        self,
        project_id: str,
        owner_id: str,
    ):
        return self.project_repository.update_project(
            project_id,
            {"owner_id": owner_id},
        )

    def set_project_lifecycle_phase(
        self,
        project_id: str,
        lifecycle_phase: str,
    ):
        normalized_phase = lifecycle_phase.strip().upper()
        return self.project_repository.update_project(
            project_id,
            {"lifecycle_phase": normalized_phase},
        )

    def get_dashboard_widgets(
        self,
        project_id: str,
    ):
        project = self.project_repository.get_project_by_id(project_id)
        if not project:
            return None

        return {
            "project_id": project_id,
            "widgets": [
                {
                    "id": "status_overview",
                    "title": "Status Overview",
                    "value": project.get("status", "UNKNOWN"),
                },
                {
                    "id": "owner",
                    "title": "Owner",
                    "value": project.get("owner_id"),
                },
                {
                    "id": "lifecycle",
                    "title": "Lifecycle Phase",
                    "value": project.get("lifecycle_phase", "UNSET"),
                },
                {
                    "id": "tags_count",
                    "title": "Tags",
                    "value": len(project.get("tags", [])),
                },
            ],
        }

    def get_cross_project_links(
        self,
        project_id: str,
    ):
        project = self.project_repository.get_project_by_id(project_id)
        if not project:
            return None

        organization_id = project.get("organization_id")
        if organization_id:
            candidates = self.project_repository.get_projects_by_organization(organization_id)
        else:
            candidates = self.project_repository.get_all_projects()

        links: list[dict] = []
        source_tags = set(project.get("tags", []))
        source_owner = project.get("owner_id")

        for candidate in candidates:
            if candidate.get("id") == project_id:
                continue

            reasons: list[str] = []
            if source_owner and candidate.get("owner_id") == source_owner:
                reasons.append("shared_owner")

            target_tags = set(candidate.get("tags", []))
            common_tags = sorted(source_tags.intersection(target_tags))
            if common_tags:
                reasons.append("shared_tags")

            if not reasons:
                continue

            links.append(
                {
                    "source_project_id": project_id,
                    "target_project_id": candidate.get("id"),
                    "target_project_name": candidate.get("project_name"),
                    "link_type": "RELATED",
                    "reasons": reasons,
                    "shared_tags": common_tags,
                }
            )

        return {
            "project_id": project_id,
            "links": links,
            "total_links": len(links),
        }

    def get_project_kpis(
        self,
        project_id: str,
    ):
        project = self.project_repository.get_project_by_id(project_id)
        if not project:
            return None

        organization_id = project.get("organization_id")
        if organization_id:
            organization_projects = self.project_repository.get_projects_by_organization(organization_id)
        else:
            organization_projects = self.project_repository.get_all_projects()

        active_count = len(
            [
                item
                for item in organization_projects
                if str(item.get("status", "")).upper() == "ACTIVE"
            ]
        )
        archived_count = len(
            [
                item
                for item in organization_projects
                if str(item.get("status", "")).upper() == "ARCHIVED"
            ]
        )

        comments_count = len(self.project_comments.get(project_id, []))
        attachments_count = len(self.project_attachments.get(project_id, []))

        return {
            "project_id": project_id,
            "kpis": [
                {"id": "organization_projects", "label": "Organization Projects", "value": len(organization_projects)},
                {"id": "active_projects", "label": "Active Projects", "value": active_count},
                {"id": "archived_projects", "label": "Archived Projects", "value": archived_count},
                {"id": "project_tags", "label": "Project Tags", "value": len(project.get("tags", []))},
                {"id": "project_comments", "label": "Project Comments", "value": comments_count},
                {"id": "project_attachments", "label": "Project Attachments", "value": attachments_count},
            ],
        }

    def get_project_analytics(
        self,
        project_id: str,
    ):
        kpis_payload = self.get_project_kpis(project_id)
        if not kpis_payload:
            return None

        values = {
            item["id"]: item["value"]
            for item in kpis_payload["kpis"]
        }

        return {
            "project_id": project_id,
            "analytics": {
                "engagement_score": values["project_comments"] * 3 + values["project_attachments"] * 2,
                "portfolio_coverage": values["organization_projects"],
                "tag_density": values["project_tags"],
                "status_distribution": {
                    "active": values["active_projects"],
                    "archived": values["archived_projects"],
                },
            },
        }

    def add_project_attachment(
        self,
        project_id: str,
        filename: str,
        uploaded_by: str,
    ):
        project = self.project_repository.get_project_by_id(project_id)
        if not project:
            return None

        attachment = {
            "id": str(uuid4()),
            "filename": filename.strip(),
            "uploaded_by": uploaded_by.strip(),
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        self.project_attachments.setdefault(project_id, []).append(attachment)
        return attachment

    def get_project_attachments(
        self,
        project_id: str,
    ):
        project = self.project_repository.get_project_by_id(project_id)
        if not project:
            return None
        return self.project_attachments.get(project_id, [])

    def add_project_comment(
        self,
        project_id: str,
        comment: str,
        author: str,
    ):
        project = self.project_repository.get_project_by_id(project_id)
        if not project:
            return None

        payload = {
            "id": str(uuid4()),
            "comment": comment.strip(),
            "author": author.strip(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.project_comments.setdefault(project_id, []).append(payload)
        return payload

    def get_project_comments(
        self,
        project_id: str,
    ):
        project = self.project_repository.get_project_by_id(project_id)
        if not project:
            return None
        return self.project_comments.get(project_id, [])

    def get_project_timeline(
        self,
        project_id: str,
    ):
        project = self.project_repository.get_project_by_id(project_id)
        if not project:
            return None

        timeline = [
            {
                "id": f"{project_id}-project-state",
                "event_type": "PROJECT_STATUS",
                "title": "Project status snapshot",
                "description": f"Current status: {project.get('status', 'UNKNOWN')}",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ]

        for comment in self.project_comments.get(project_id, []):
            timeline.append(
                {
                    "id": comment["id"],
                    "event_type": "COMMENT",
                    "title": "Project comment added",
                    "description": comment["comment"],
                    "author": comment["author"],
                    "created_at": comment["created_at"],
                }
            )

        for attachment in self.project_attachments.get(project_id, []):
            timeline.append(
                {
                    "id": attachment["id"],
                    "event_type": "ATTACHMENT",
                    "title": "Attachment uploaded",
                    "description": attachment["filename"],
                    "author": attachment["uploaded_by"],
                    "created_at": attachment["uploaded_at"],
                }
            )

        timeline.sort(key=lambda event: event["created_at"], reverse=True)
        return {"project_id": project_id, "events": timeline}

    def _normalize_tags(
        self,
        tags: list[str] | None,
    ) -> list[str]:
        if not tags:
            return []

        unique_tags: list[str] = []

        for tag in tags:
            normalized = tag.strip().lower()
            if normalized and normalized not in unique_tags:
                unique_tags.append(normalized)

        return unique_tags