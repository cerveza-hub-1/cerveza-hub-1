import os
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, jsonify

from app import create_app
from app.modules.zenodo.forms import ZenodoForm
from app.modules.zenodo.services import ZenodoService
from core.configuration.configuration import uploads_folder_name


@pytest.fixture
def service():
    # Forzar modo fakenodo para simplificar
    os.environ["FAKENODO_URL"] = "http://localhost:5000/fakenodo/api/records"
    return ZenodoService()


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as client:
        yield client


@pytest.fixture(scope="module")
def app_context():
    app = create_app()
    with app.app_context():
        yield app


def test_get_zenodo_url_fakenodo(service):
    assert service.get_zenodo_url().startswith("http://localhost")


def test_get_zenodo_url_env_development(monkeypatch):
    monkeypatch.delenv("FAKENODO_URL", raising=False)
    monkeypatch.setenv("FLASK_ENV", "development")
    s = ZenodoService()
    assert "sandbox.zenodo.org" in s.get_zenodo_url()


def test_get_zenodo_url_env_production(monkeypatch):
    monkeypatch.delenv("FAKENODO_URL", raising=False)
    monkeypatch.setenv("FLASK_ENV", "production")
    s = ZenodoService()
    assert "zenodo.org" in s.get_zenodo_url()


def test_get_zenodo_access_token(monkeypatch):
    monkeypatch.setenv("ZENODO_ACCESS_TOKEN", "abc123")
    s = ZenodoService()
    assert s.get_zenodo_access_token() == "abc123"


def test_test_connection_success(service):
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        assert service.test_connection() is True


def test_test_connection_failure(service):
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 500
        assert service.test_connection() is False


def test_test_full_connection_success(service, tmp_path, app_context):
    monkey_file = tmp_path / "test_file.txt"
    monkey_file.write_text("dummy")

    with patch("requests.post") as mock_post, patch("requests.delete") as mock_delete:
        mock_post.side_effect = [
            MagicMock(status_code=201, json=lambda: {"id": 1}),
            MagicMock(status_code=201, json=lambda: {"ok": True}),
        ]
        mock_delete.return_value.status_code = 204

        # Aquí ya hay contexto de Flask
        resp = service.test_full_connection()
        data = resp.get_json()
        assert data["success"] is True


def test_test_full_connection_create_fail(service, app_context):
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 400
        resp = service.test_full_connection()
        data = resp.get_json()
        assert data["success"] is False


def test_get_all_depositions_success(service):
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"records": []}
        result = service.get_all_depositions()
        assert "records" in result


def test_get_all_depositions_failure(service):
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 500
        with pytest.raises(Exception):
            service.get_all_depositions()


def make_dataset():
    ds_meta = MagicMock()
    ds_meta.title = "Title"
    ds_meta.description = "Desc"
    ds_meta.authors = [MagicMock(name="John")]
    ds_meta.tags = "tag1, tag2"
    dataset = MagicMock()
    dataset.ds_meta_data = ds_meta
    dataset.id = 1
    return dataset


def test_create_new_deposition_success(service):
    dataset = make_dataset()
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"id": 1}
        result = service.create_new_deposition(dataset)
        assert result["id"] == 1


def test_create_new_deposition_failure(service):
    dataset = make_dataset()
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = "error"
        with pytest.raises(Exception):
            service.create_new_deposition(dataset)


def make_csvmodel():
    fm_meta = MagicMock()
    fm_meta.csv_filename = "file.csv"
    csv_model = MagicMock()
    csv_model.fm_meta_data = fm_meta
    return csv_model


def test_upload_file_fakenodo_success(service):
    dataset = make_dataset()
    csv_model = make_csvmodel()
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ok": True}
        result = service.upload_file(dataset, 1, csv_model, user=MagicMock(id=1))
        assert result["ok"] is True


def test_upload_file_fakenodo_fallback(service, tmp_path):
    dataset = make_dataset()
    csv_model = make_csvmodel()
    file_path = tmp_path / "file.csv"
    file_path.write_text("dummy")
    with (
        patch("requests.post") as mock_post,
        patch(
            "core.configuration.configuration.uploads_folder_name",
            return_value=str(tmp_path),
        ),
    ):
        mock_post.return_value.status_code = 400
        result = service.upload_file(dataset, 1, csv_model, user=MagicMock(id=1))
        assert result["checksum"] == "simulated"


def test_publish_deposition_fakenodo(service):
    with patch("requests.post") as mock_post:
        mock_post.return_value.json.return_value = {"published": True}
        result = service.publish_deposition(1)
        assert result["published"] is True


def test_publish_deposition_real_failure(monkeypatch):
    monkeypatch.delenv("FAKENODO_URL", raising=False)
    s = ZenodoService()
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = "error"
        with pytest.raises(Exception):
            s.publish_deposition(1)


def test_get_deposition_fakenodo(service):
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"id": 1}
        result = service.get_deposition(1)
        assert result["id"] == 1


def test_get_deposition_real_failure(monkeypatch):
    monkeypatch.delenv("FAKENODO_URL", raising=False)
    s = ZenodoService()
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 400
        with pytest.raises(Exception):
            s.get_deposition(1)


def test_get_doi(service):
    with patch.object(service, "get_deposition", return_value={"doi": "10.1234/abc"}):
        doi = service.get_doi(1)
        assert doi == "10.1234/abc"


def test_get_record_url_fakenodo(service):
    url = service.get_record_url(1)
    assert "/records/1" in url


def test_get_record_url_production(monkeypatch):
    monkeypatch.delenv("FAKENODO_URL", raising=False)
    monkeypatch.setenv("FLASK_ENV", "production")
    s = ZenodoService()
    url = s.get_record_url(1)
    assert "zenodo.org/records/1" in url


def test_get_record_url_development(monkeypatch):
    monkeypatch.delenv("FAKENODO_URL", raising=False)
    monkeypatch.setenv("FLASK_ENV", "development")
    s = ZenodoService()
    url = s.get_record_url(1)
    assert "sandbox.zenodo.org/records/1" in url


def test_zenodo_form_has_submit():
    app = Flask(__name__)
    app.secret_key = "test"
    with app.test_request_context():
        form = ZenodoForm()
        assert hasattr(form, "submit")
        assert form.submit.label.text == "Save zenodo"


def test_zenodo_index_route(client):
    response = client.get("/zenodo")
    assert response.status_code == 200
    assert b"<html" in response.data or b"Zenodo" in response.data


def test_zenodo_test_route(client, app_context):
    with patch(
        "app.modules.zenodo.routes.ZenodoService.test_full_connection",
        return_value=jsonify({"success": True, "messages": []}),
    ):
        response = client.get("/zenodo/test")
        assert response.status_code == 200
        assert response.get_json()["success"] is True


def test_test_full_connection_logs_and_cleanup(service, tmp_path, app_context):
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("dummy")

    with patch("requests.post") as mock_post, patch("requests.delete") as mock_delete:
        mock_post.side_effect = [
            MagicMock(status_code=201, json=lambda: {"id": 1}),
            MagicMock(status_code=201, json=lambda: {"ok": True}),
        ]
        mock_delete.return_value.status_code = 204

        response = service.test_full_connection()
        data = response.get_json()
        assert data["success"] is True


def test_test_full_connection_file_missing(service, tmp_path, app_context):
    with patch("requests.post") as mock_post, patch("requests.delete") as mock_delete:
        mock_post.side_effect = [
            MagicMock(status_code=201, json=lambda: {"id": 1}),
            MagicMock(status_code=201, json=lambda: {"ok": True}),
        ]
        mock_delete.return_value.status_code = 204

        # Eliminar el archivo antes de llamar
        file_path = os.path.join(os.getenv("WORKING_DIR", ""), "test_file.txt")
        if os.path.exists(file_path):
            os.remove(file_path)

        response = service.test_full_connection()
        data = response.get_json()
        assert data["success"] is True


def make_dataset_and_csv(tmp_path):
    # Dataset simulado
    ds_meta = MagicMock()
    ds_meta.title = "Title"
    ds_meta.description = "Desc"
    ds_meta.authors = []
    ds_meta.tags = ""
    dataset = MagicMock()
    dataset.ds_meta_data = ds_meta
    dataset.id = 1

    # CSVModel simulado
    fm_meta = MagicMock()
    fm_meta.csv_filename = "file.csv"
    csv_model = MagicMock()
    csv_model.fm_meta_data = fm_meta

    # Crear archivo en la ruta esperada
    user_id = 1
    file_dir = os.path.join(uploads_folder_name(), f"user_{user_id}", f"dataset_{dataset.id}")
    os.makedirs(file_dir, exist_ok=True)
    file_path = os.path.join(file_dir, fm_meta.csv_filename)
    with open(file_path, "w") as f:
        f.write("dummy content")

    return dataset, csv_model, user_id, file_path


def test_upload_file_zenodo_real_success(monkeypatch, tmp_path):
    # Forzar Zenodo real
    monkeypatch.delenv("FAKENODO_URL", raising=False)
    service = ZenodoService()

    dataset, csv_model, user_id, file_path = make_dataset_and_csv(tmp_path)

    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"uploaded": True}

        result = service.upload_file(dataset, 123, csv_model, user=MagicMock(id=user_id))
        assert result["uploaded"] is True


def test_upload_file_zenodo_real_failure(monkeypatch, tmp_path):
    # Forzar Zenodo real
    monkeypatch.delenv("FAKENODO_URL", raising=False)
    service = ZenodoService()

    dataset, csv_model, user_id, file_path = make_dataset_and_csv(tmp_path)

    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {"error": "bad request"}

        with pytest.raises(Exception) as excinfo:
            service.upload_file(dataset, 123, csv_model, user=MagicMock(id=user_id))
        assert "Failed to upload files" in str(excinfo.value)