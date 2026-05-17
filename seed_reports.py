from app.repositories.project_repository import (
    ProjectRepository
)
from app.repositories.report_repository import (
    ReportRepository
)

project_repository = ProjectRepository()
report_repository = ReportRepository()

projects = project_repository.get_all_projects()

project_map = {
    project["project_name"]: project["id"]
    for project in projects
}

reports = [
    {
        "project_name": "מגדלי הצפון",
        "file_name": "weekly_report_migdaley_hatzafon.pdf",
        "received_date": "2026-05-14"
    },
    {
        "project_name": "פארק הים",
        "file_name": "weekly_report_park_hayam.pdf",
        "received_date": "2026-05-14"
    }
]

for report in reports:
    project_id = project_map.get(
        report["project_name"]
    )

    if not project_id:
        continue

    report_repository.create_report(
        project_id=project_id,
        file_name=report["file_name"],
        received_date=report["received_date"]
    )

print("Reports seeded.")