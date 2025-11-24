import pytest

from app import create_app
import app.modules.dataset.routes as dataset_routes


@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as client:
        yield client


def test_get_most_downloaded_datasets_success(client, monkeypatch):
    """Endpoint should return JSON list and HTTP 200 when service succeeds."""
    sample = [
        {"id": 1, "title": "Dataset A", "downloads": 10},
        {"id": 2, "title": "Dataset B", "downloads": 5},
    ]

    class StubService:
        def get_most_downloaded_datasets(self, limit=5):
            return sample

    monkeypatch.setattr(dataset_routes, "dataset_service", StubService())

    resp = client.get("/dataset/ranking/downloads")
    assert resp.status_code == 200
    assert resp.get_json() == sample


def test_get_most_viewed_datasets_success(client, monkeypatch):
    """Endpoint should return JSON list and HTTP 200 when service succeeds."""
    sample = [
        {"id": 3, "title": "Dataset C", "views": 20},
        {"id": 4, "title": "Dataset D", "views": 7},
    ]

    class StubService:
        def get_most_viewed_datasets(self, limit=5):
            return sample

    monkeypatch.setattr(dataset_routes, "dataset_service", StubService())

    resp = client.get("/dataset/ranking/views")
    assert resp.status_code == 200
    assert resp.get_json() == sample


def test_get_most_downloaded_datasets_failure(client, monkeypatch):
    """Endpoint should return HTTP 500 and error message when service raises."""

    class StubService:
        def get_most_downloaded_datasets(self, limit=5):
            raise RuntimeError("database error")

    monkeypatch.setattr(dataset_routes, "dataset_service", StubService())

    resp = client.get("/dataset/ranking/downloads")
    assert resp.status_code == 500
    data = resp.get_json()
    assert isinstance(data, dict)
    assert data.get("message") == "Failed to get ranking"
