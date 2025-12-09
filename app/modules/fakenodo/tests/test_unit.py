from unittest.mock import patch

import pytest

from app import create_app
from app.modules.fakenodo.models import Fakenodo
from app.modules.fakenodo.repositories import FakenodoRepository
from app.modules.fakenodo.services import FakenodoService


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as client:
        yield client


def test_add_version_unpublished():
    f = Fakenodo(id=1, meta={"title": "Test"})
    version = f.add_version(meta={"title": "v1"}, published=False)
    assert version["doi"] is None
    assert version["published"] is False
    assert version in f.versions


def test_add_version_published_generates_doi():
    f = Fakenodo(id=1, meta={"title": "Test"})
    version = f.add_version(meta={"title": "v2"}, published=True)
    assert version["doi"].startswith("10.9999/fakenodo.")
    assert version["published"] is True


def test_to_dict_structure():
    f = Fakenodo(id=1, meta={"title": "Test"})
    f.add_version(meta={"title": "v1"})
    result = f.to_dict()
    assert result["id"] == 1
    assert "meta" in result
    assert isinstance(result["versions"], list)


def test_create_record_adds_first_version():
    repo = FakenodoRepository()
    record = repo.create(meta={"title": "Test"})
    assert record.id == 1
    assert len(record.versions) == 1
    assert record.versions[0]["published"] is False


def test_get_or_404_success():
    repo = FakenodoRepository()
    record = repo.create(meta={"title": "Test"})
    fetched = repo.get_or_404(record.id)
    assert fetched == record


def test_get_or_404_failure():
    repo = FakenodoRepository()
    with pytest.raises(KeyError):
        repo.get_or_404(999)


def test_list_all_returns_dicts():
    repo = FakenodoRepository()
    repo.create(meta={"title": "Test"})
    result = repo.list_all()
    assert isinstance(result, list)
    assert "id" in result[0]


def test_create_record_returns_dict():
    service = FakenodoService()
    record = service.create_record({"title": "Test"})
    assert "id" in record
    assert "versions" in record


def test_publish_record_adds_new_version():
    service = FakenodoService()
    record = service.create_record({"title": "Test"})
    version = service.publish_record(record["id"], files=["file1.txt"])
    assert version["published"] is True
    assert version["doi"].startswith("10.9999/fakenodo.")


def test_list_versions_returns_all_versions():
    service = FakenodoService()
    record = service.create_record({"title": "Test"})
    versions = service.list_versions(record["id"])
    assert isinstance(versions, list)
    assert len(versions) >= 1


def test_index_route(client):
    response = client.get("/fakenodo/")
    assert response.status_code == 200
    assert b"Bienvenido" in response.data or b"<html" in response.data


def test_create_record_route(client):
    response = client.post("/fakenodo/api/records", json={"meta": {"title": "Test"}})
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data


def test_publish_record_route(client):
    create_resp = client.post("/fakenodo/api/records", json={"meta": {"title": "Test"}})
    record_id = create_resp.get_json()["id"]

    publish_resp = client.post(f"/fakenodo/api/records/{record_id}/actions/publish", json={"files": ["file1.txt"]})
    assert publish_resp.status_code == 202
    version = publish_resp.get_json()
    assert version["published"] is True


def test_list_versions_route(client):
    create_resp = client.post("/fakenodo/api/records", json={"meta": {"title": "Test"}})
    record_id = create_resp.get_json()["id"]

    response = client.get(f"/fakenodo/api/records/{record_id}/versions")
    assert response.status_code == 200
    versions = response.get_json()
    assert isinstance(versions, list)


def test_upload_files_route(client):
    create_resp = client.post("/fakenodo/api/records", json={"meta": {"title": "Test"}})
    record_id = create_resp.get_json()["id"]

    response = client.post(f"/fakenodo/api/records/{record_id}/files", json={"files": ["file1.txt"]})
    assert response.status_code == 201
    assert response.get_json()["message"].startswith("File uploaded")


def test_delete_record_route(client):
    create_resp = client.post("/fakenodo/api/records", json={"meta": {"title": "Test"}})
    record_id = create_resp.get_json()["id"]

    response = client.delete(f"/fakenodo/api/records/{record_id}")
    assert response.status_code == 200
    assert response.get_json()["message"].startswith("Record deleted")


def test_fakenodo_test_route(client):
    response = client.get("/fakenodo/test")
    assert response.status_code == 200
    data = response.get_json()
    assert "success" in data
    assert isinstance(data["messages"], list)


def test_publish_record_invalid_id(client):
    response = client.post("/fakenodo/api/records/999/actions/publish", json={"files": ["file.txt"]})
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_full_connection_failure(client):
    with patch("app.modules.fakenodo.repositories.FakenodoRepository.create", return_value=None):
        response = client.get("/fakenodo/test")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False
        assert "Failed to create simulated deposition." in data["messages"]


def test_list_versions_invalid_id(client):
    response = client.get("/fakenodo/api/records/999/versions")
    assert response.status_code in (404, 500)
