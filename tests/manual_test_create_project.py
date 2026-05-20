from app.services.project_service import (
    ProjectService
)


service = (
    ProjectService()
)

result = (
    service.create_project(
        project_name=
            "בניין A",

        supervisor_name=
            "ארז שמאי",

        supervisor_email=
            "erez@example.com",
    )
)

print("\n=== CREATED PROJECT ===\n")

print(result)

print()