from app.repositories.project_repository import (
    ProjectRepository
)

repository = ProjectRepository()

projects = [
    {
        "project_name": "מגדלי הצפון",
        "supervisor_name": "יוסי כהן",
        "supervisor_email": "yossi@example.com"
    },
    {
        "project_name": "גני השרון",
        "supervisor_name": "דני לוי",
        "supervisor_email": "danny@example.com"
    },
    {
        "project_name": "פארק הים",
        "supervisor_name": "רועי ישראלי",
        "supervisor_email": "roee@example.com"
    }
]

for project in projects:
    repository.create_project(
        project_name=
        project["project_name"],

        supervisor_name=
        project["supervisor_name"],

        supervisor_email=
        project["supervisor_email"]
    )

print("Seed completed.")