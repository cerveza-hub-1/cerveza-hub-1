from unittest.mock import MagicMock, patch

import pytest

import app.modules.dataset.routes as dataset_routes
from app import create_app
from app.modules.dataset.services import DataSetService


@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as client:
        yield client


def test_get_most_downloaded_datasets_success(client, monkeypatch):
    """Test unitario de servicio que valida el endpoint cuando el servicio funciona correctamente."""
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
    """Test unitario de servicio que valida el endponit cuando el servicio funciona correctamente."""
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
    """Test unitario de servicio que valida el endpoint cuando el servicio falla."""

    class StubService:
        def get_most_downloaded_datasets(self, limit=5):
            raise RuntimeError("database error")

    monkeypatch.setattr(dataset_routes, "dataset_service", StubService())

    resp = client.get("/dataset/ranking/downloads")
    assert resp.status_code == 500
    data = resp.get_json()
    assert isinstance(data, dict)
    assert data.get("message") == "Failed to get ranking"


# Test unitario para DataSetService.get_most_viewed_datasets que valida la lógica interna
def test_get_most_viewed_datasets_unit():
    service = DataSetService()

    # Datos simulados que "devolvería" la base de datos
    fake_results = [
        MagicMock(id=1, title="Dataset A", doi="doi-a", views=15),
        MagicMock(id=2, title="Dataset B", doi="doi-b", views=12),
        MagicMock(id=3, title="Dataset C", doi="doi-c", views=12),
        MagicMock(id=4, title="Dataset D", doi="doi-d", views=11),
        MagicMock(id=5, title="Dataset E", doi="doi-e", views=10),
        MagicMock(id=6, title="Dataset F", doi="doi-f", views=3),
        MagicMock(id=7, title="Dataset G", doi="doi-g", views=2),
        MagicMock(id=8, title="Dataset H", doi="doi-h", views=1),
        MagicMock(id=9, title="Dataset I", doi="doi-i", views=0),
        MagicMock(id=10, title="Dataset J", doi="doi-j", views=0),
    ]

    with patch("app.modules.dataset.services.db.session") as mock_session:
        mock_query = MagicMock()

        # Configurar la cadena de métodos de la base de datos simulada
        mock_query.join.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = fake_results

        mock_session.query.return_value = mock_query

        # Ejecutar el método
        result = service.get_most_viewed_datasets(limit=10)

    # Validar salida final
    assert result == [
        {"id": 1, "title": "Dataset A", "views": 15, "doi": "doi-a"},
        {"id": 2, "title": "Dataset B", "views": 12, "doi": "doi-b"},
        {"id": 3, "title": "Dataset C", "views": 12, "doi": "doi-c"},
        {"id": 4, "title": "Dataset D", "views": 11, "doi": "doi-d"},
        {"id": 5, "title": "Dataset E", "views": 10, "doi": "doi-e"},
        {"id": 6, "title": "Dataset F", "views": 3, "doi": "doi-f"},
        {"id": 7, "title": "Dataset G", "views": 2, "doi": "doi-g"},
        {"id": 8, "title": "Dataset H", "views": 1, "doi": "doi-h"},
        {"id": 9, "title": "Dataset I", "views": 0, "doi": "doi-i"},
        {"id": 10, "title": "Dataset J", "views": 0, "doi": "doi-j"},
    ]

    # Validar llamadas clave
    mock_session.query.assert_called()
    mock_query.limit.assert_called_once_with(10)
    mock_query.order_by.assert_called_once()
    mock_query.all.assert_called_once()


def test_get_most_downloaded_datasets_unit():
    service = DataSetService()

    # Datos simulados devueltos por SQLAlchemy
    fake_results = [
        MagicMock(id=1, title="Dataset A", doi="doi-a", downloads=15),
        MagicMock(id=2, title="Dataset B", doi="doi-b", downloads=12),
        MagicMock(id=3, title="Dataset C", doi="doi-c", downloads=12),
        MagicMock(id=4, title="Dataset D", doi="doi-d", downloads=11),
        MagicMock(id=5, title="Dataset E", doi="doi-e", downloads=10),
        MagicMock(id=6, title="Dataset F", doi="doi-f", downloads=3),
        MagicMock(id=7, title="Dataset G", doi="doi-g", downloads=2),
        MagicMock(id=8, title="Dataset H", doi="doi-h", downloads=1),
        MagicMock(id=9, title="Dataset I", doi="doi-i", downloads=0),
        MagicMock(id=10, title="Dataset J", doi="doi-j", downloads=0),
    ]

    with patch("app.modules.dataset.services.db.session") as mock_session:
        mock_query = MagicMock()

        # Encadenado de métodos típico de SQLAlchemy
        mock_query.join.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = fake_results

        mock_session.query.return_value = mock_query

        # Ejecutar la función
        result = service.get_most_downloaded_datasets(limit=5)

    # Validar salida final transformada
    assert result == [
        {"id": 1, "title": "Dataset A", "downloads": 15, "doi": "doi-a"},
        {"id": 2, "title": "Dataset B", "downloads": 12, "doi": "doi-b"},
        {"id": 3, "title": "Dataset C", "downloads": 12, "doi": "doi-c"},
        {"id": 4, "title": "Dataset D", "downloads": 11, "doi": "doi-d"},
        {"id": 5, "title": "Dataset E", "downloads": 10, "doi": "doi-e"},
        {"id": 6, "title": "Dataset F", "downloads": 3, "doi": "doi-f"},
        {"id": 7, "title": "Dataset G", "downloads": 2, "doi": "doi-g"},
        {"id": 8, "title": "Dataset H", "downloads": 1, "doi": "doi-h"},
        {"id": 9, "title": "Dataset I", "downloads": 0, "doi": "doi-i"},
        {"id": 10, "title": "Dataset J", "downloads": 0, "doi": "doi-j"},
    ]

    mock_session.query.assert_called()
    mock_query.limit.assert_called_once_with(5)
    mock_query.order_by.assert_called_once()
    mock_query.all.assert_called_once()
