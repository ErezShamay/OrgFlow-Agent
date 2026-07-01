from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.quality_issue_photo_service import (
    QualityIssuePhotoService,
)
from app.services.quality_issue_service import QualityIssueService
from tests.quality_issues_test_support import (
    FakeProjectRepository,
    InMemoryQualityIssueEventRepository,
    InMemoryQualityIssuePhotoRepository,
    InMemoryQualityIssueRepository,
    qc_issue_payload,
)
from tests.test_quality_issues import _auth_headers


@pytest.fixture
def qc_photo_setup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[TestClient, QualityIssueService, InMemoryQualityIssuePhotoRepository]:
    photo_repo = InMemoryQualityIssuePhotoRepository()
    service = QualityIssueService(
        issue_repository=InMemoryQualityIssueRepository(),
        event_repository=InMemoryQualityIssueEventRepository(),
        project_repository=FakeProjectRepository(),
        photo_repository=photo_repo,
        photo_service=QualityIssuePhotoService(photos_root=tmp_path),
    )
    monkeypatch.setattr("app.dependencies.quality_issue_service", service)
    return TestClient(app), service, photo_repo


def _create_in_remediation_issue(client: TestClient) -> dict:
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=qc_issue_payload(),
    ).json()
    client.patch(
        f"/issues/{created['id']}",
        headers=_auth_headers("SUPERVISOR"),
        json={"status": "IN_REMEDIATION"},
    )
    return created


def test_upload_remediation_photo_returns_photo_id(
    qc_photo_setup: tuple[
        TestClient,
        QualityIssueService,
        InMemoryQualityIssuePhotoRepository,
    ],
) -> None:
    client, _service, photo_repo = qc_photo_setup
    created = _create_in_remediation_issue(client)

    response = client.post(
        f"/issues/{created['id']}/photos",
        headers=_auth_headers("CONTRACTOR"),
        files={
            "file": ("remediation.jpg", b"fake-jpeg-bytes", "image/jpeg"),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["issue_id"] == created["id"]
    assert body["photo_id"]
    assert body["url"] == f"/issues/{created['id']}/photos/{body['photo_id']}"
    assert body["photo_id"] in photo_repo.records


def test_get_remediation_photo_bytes(
    qc_photo_setup: tuple[
        TestClient,
        QualityIssueService,
        InMemoryQualityIssuePhotoRepository,
    ],
) -> None:
    client, _service, _photo_repo = qc_photo_setup
    created = _create_in_remediation_issue(client)

    upload = client.post(
        f"/issues/{created['id']}/photos",
        headers=_auth_headers("CONTRACTOR"),
        files={
            "file": ("remediation.jpg", b"fake-jpeg-bytes", "image/jpeg"),
        },
    ).json()

    photo_response = client.get(
        upload["url"],
        headers=_auth_headers("CONTRACTOR"),
    )
    assert photo_response.status_code == 200
    assert photo_response.content == b"fake-jpeg-bytes"


def test_contractor_remediation_requires_uploaded_photo(
    qc_photo_setup: tuple[
        TestClient,
        QualityIssueService,
        InMemoryQualityIssuePhotoRepository,
    ],
) -> None:
    client, service, _photo_repo = qc_photo_setup
    created = _create_in_remediation_issue(client)

    missing_photo = client.patch(
        f"/issues/{created['id']}",
        headers=_auth_headers("CONTRACTOR"),
        json={"status": "PENDING_VERIFICATION"},
    )
    assert missing_photo.status_code == 400

    upload = client.post(
        f"/issues/{created['id']}/photos",
        headers=_auth_headers("CONTRACTOR"),
        files={
            "file": ("remediation.jpg", b"fake-jpeg-bytes", "image/jpeg"),
        },
    ).json()

    submit = client.patch(
        f"/issues/{created['id']}",
        headers=_auth_headers("CONTRACTOR"),
        json={
            "status": "PENDING_VERIFICATION",
            "photo_ids": [upload["photo_id"]],
            "notes": "בוצע תיקון",
        },
    )
    assert submit.status_code == 200
    assert submit.json()["status"] == "PENDING_VERIFICATION"
    assert upload["photo_id"] in submit.json()["photo_ids"]

    detail = client.get(
        f"/issues/{created['id']}",
        headers=_auth_headers("SUPERVISOR"),
    ).json()
    remediation_events = [
        event
        for event in detail["events"]
        if event["event_type"] == "REMEDIATION_SUBMITTED"
    ]
    assert remediation_events[0]["payload"]["photo_ids"] == [upload["photo_id"]]
    assert remediation_events[0]["payload"]["notes"] == "בוצע תיקון"


def test_upload_remediation_photo_rejected_when_issue_not_in_remediation(
    qc_photo_setup: tuple[
        TestClient,
        QualityIssueService,
        InMemoryQualityIssuePhotoRepository,
    ],
) -> None:
    client, _service, _photo_repo = qc_photo_setup
    created = client.post(
        "/projects/proj-1/issues",
        headers=_auth_headers("SUPERVISOR"),
        json=qc_issue_payload(),
    ).json()

    response = client.post(
        f"/issues/{created['id']}/photos",
        headers=_auth_headers("CONTRACTOR"),
        files={
            "file": ("remediation.jpg", b"fake-jpeg-bytes", "image/jpeg"),
        },
    )
    assert response.status_code == 400
