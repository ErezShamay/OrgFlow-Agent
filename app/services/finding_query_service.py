from app.repositories.finding_repository import (
    FindingRepository
)


class FindingQueryService:

    def __init__(self):

        self.finding_repository = (
            FindingRepository()
        )

    def get_project_findings(
        self,
        project_id: str
    ):

        return (
            self.finding_repository
            .get_findings_by_project(
                project_id
            )
        )

    def get_schedule_delays(self):

        return (
            self.finding_repository
            .get_findings_by_type(
                "schedule_delay"
            )
        )

    def get_critical_findings(self):

        return (
            self.finding_repository
            .get_findings_by_severity(
                "critical"
            )
        )

    def get_open_findings(self):

        return (
            self.finding_repository
            .get_open_findings()
        )