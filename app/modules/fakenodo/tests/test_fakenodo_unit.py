import io
from unittest.mock import MagicMock, patch

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


# -----------------------------
# Model: Fakenodo
# -----------------------------


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


# -----------------------------
# Repository: FakenodoRepository
# -----------------------------


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


# -----------------------------
# Service: FakenodoService
# -----------------------------


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


def test_publish_record_invalid_files_type():
    service = FakenodoService()
    record = service.create_record({"title": "Test"})
    version = service.publish_record(record["id"], files="notalist")
    assert isinstance(version["files"], list)


def test_list_versions_returns_all_versions():
    service = FakenodoService()
    record = service.create_record({"title": "Test"})
    versions = service.list_versions(record["id"])
    assert isinstance(versions, list)
    assert len(versions) >= 1


def test_get_record_collects_files():
    service = FakenodoService()
    record = service.create_record({"title": "Test"})
    service.publish_record(record["id"], files=["a.txt", "b.txt"])
    result = service.get_record(record["id"])
    assert "files" in result
    assert set(result["files"]) == {"a.txt", "b.txt"}


def test_list_all_service():
    service = FakenodoService()
    service.create_record({"title": "Test"})
    records = service.list_all()
    assert isinstance(records, list)


# -----------------------------
# Routes: Flask endpoints
# -----------------------------


def test_index_route(client):
    response = client.get("/fakenodo/")
    assert response.status_code == 200


def test_create_record_route(client):
    response = client.post("/fakenodo/api/records", json={"meta": {"title": "Test"}})
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data


def test_get_record_route(client):
    create_resp = client.post("/fakenodo/api/records", json={"meta": {"title": "Test"}})
    record_id = create_resp.get_json()["id"]

    response = client.get(f"/fakenodo/api/records/{record_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert "id" in data


def test_get_record_route_invalid(client):
    response = client.get("/fakenodo/api/records/999")
    assert response.status_code == 404


def test_publish_record_route(client):
    create_resp = client.post("/fakenodo/api/records", json={"meta": {"title": "Test"}})
    record_id = create_resp.get_json()["id"]

    publish_resp = client.post(
        f"/fakenodo/api/records/{record_id}/actions/publish",
        json={"files": ["file1.txt"]},
    )
    assert publish_resp.status_code == 202
    version = publish_resp.get_json()
    assert version["published"] is True


def test_publish_record_invalid_id(client):
    response = client.post("/fakenodo/api/records/999/actions/publish", json={"files": ["file.txt"]})
    assert response.status_code == 404


def test_upload_files_route_json(client):
    create_resp = client.post("/fakenodo/api/records", json={"meta": {"title": "Test"}})
    record_id = create_resp.get_json()["id"]

    response = client.post(f"/fakenodo/api/records/{record_id}/files", json={"files": ["file1.txt"]})
    assert response.status_code == 201
    assert "Files uploaded" in response.get_json()["message"]


def test_upload_files_route_invalid_id(client):
    response = client.post("/fakenodo/api/records/999/files", json={"files": ["file.txt"]})
    assert response.status_code == 404


def test_list_records_route(client):
    response = client.get("/fakenodo/api/records")
    assert response.status_code == 200
    data = response.get_json()
    assert "records" in data


def test_view_record_page(client):
    create_resp = client.post("/fakenodo/api/records", json={"meta": {"title": "Test"}})
    record_id = create_resp.get_json()["id"]

    response = client.get(f"/fakenodo/records/{record_id}")
    assert response.status_code == 200
    assert b"<html" in response.data or b"error" in response.data


def test_view_record_page_invalid(client):
    response = client.get("/fakenodo/records/999")
    assert response.status_code == 200
    assert b"error" in response.data


def test_upload_files_form_file(client):
    create_resp = client.post("/fakenodo/api/records", json={"meta": {"title": "Test"}})
    record_id = create_resp.get_json()["id"]

    data = {
        "name": "custom_name.txt",
        "file": (io.BytesIO(b"dummy content"), "original.txt"),
    }

    response = client.post(
        f"/fakenodo/api/records/{record_id}/files",
        data=data,
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    json_data = response.get_json()
    assert "custom_name.txt" in json_data["files"]


def test_view_record_page_with_dataset(client):
    with patch("app.modules.fakenodo.routes.DSMetaData") as MockDSMetaData:
        mock_file = MagicMock()
        mock_file.name = "data.csv"
        mock_file.get_formatted_size.return_value = "1 KB"
        mock_file.id = 123

        mock_csv_model = MagicMock()
        mock_csv_model.files = [mock_file]

        mock_dataset = MagicMock()
        mock_dataset.id = 1
        mock_dataset.csv_models = [mock_csv_model]

        mock_ds_meta = MagicMock()
        mock_ds_meta.dataset_doi = "10.9999/fakenodo.mockdoi"
        mock_ds_meta.data_set = mock_dataset
        mock_ds_meta.title = "Mock Dataset"

        MockDSMetaData.query.filter_by.return_value.first.return_value = mock_ds_meta

        create_resp = client.post("/fakenodo/api/records", json={"meta": {"title": "Test"}})
        record_id = create_resp.get_json()["id"]
        client.post(
            f"/fakenodo/api/records/{record_id}/actions/publish",
            json={"files": ["data.csv"]},
        )

        response = client.get(f"/fakenodo/records/{record_id}")
        assert response.status_code == 200
        assert b"data.csv" in response.data


def test_upload_files_raises_exception(client):
    create_resp = client.post("/fakenodo/api/records", json={"meta": {"title": "Test"}})
    record_id = create_resp.get_json()["id"]

    # Parchear el método get_or_404 de la instancia service usada en routes.py
    with patch(
        "app.modules.fakenodo.routes.service.repository.get_or_404",
        side_effect=Exception("Simulated failure"),
    ):
        response = client.post(f"/fakenodo/api/records/{record_id}/files", json={"files": ["broken.txt"]})
        assert response.status_code == 500
        assert "Simulated failure" in response.get_json()["error"]


def test_view_record_page_exception(client):
    with patch("app.modules.fakenodo.routes.service.get_record", side_effect=Exception("Boom")):
        response = client.get("/fakenodo/records/999")
        assert response.status_code == 200
        assert b"Boom" in response.data or b"error" in response.data
