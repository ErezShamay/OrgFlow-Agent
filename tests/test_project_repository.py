from app.repositories.project_repository import (
    ProjectRepository
)


def test_create_and_fetch_projects():
    repository = ProjectRepository()

    repository.create_project(
        project_name="מגדלי הצפון",
        supervisor_name="יוסי כהן"
    )

    projects = repository.get_all_projects()

    assert len(projects) > 0