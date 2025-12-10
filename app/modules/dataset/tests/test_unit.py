import pytest

import app.modules.dataset.routes as dataset_routes
from app import create_app


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


def test_explore_post(client, monkeypatch):

    class FakeDataset:
        def __init__(self, id):
            self.id = id

        def to_dict(self):
            return {"id": self.id}

    def fake_filter(**criteria):
        assert criteria == {"query": "siu"}
        return [FakeDataset(1), FakeDataset(2)]

    monkeypatch.setattr(explore_routes.ExploreService, "filter", staticmethod(fake_filter))

    response = client.post("/explore", json={"query": "siu"})

    assert response.status_code == 200
    assert response.get_json() == [{"id": 1}, {"id": 2}]
