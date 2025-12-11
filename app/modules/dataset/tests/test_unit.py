import os
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from werkzeug.datastructures import FileStorage

import app.modules.dataset.routes as dataset_routes
from app import create_app
from app.modules.dataset.csv_validator import validate_csv_content
from app.modules.dataset.services import DataSetService


@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def client(monkeypatch):
    """Crea un cliente Flask de pruebas con un usuario autenticado falso."""
    app = create_app()
    app.testing = True

    class DummyUser:
        id = 10

        @property
        def is_authenticated(self):
            return True

        @property
        def is_active(self):
            return True

        @property
        def is_anonymous(self):
            return False

        def temp_folder(self):
            return "/tmp/datasets_test"

        def get_id(self):
            return str(self.id)

    # Sustituir current_user por DummyUser
    monkeypatch.setattr("flask_login.utils._get_user", lambda: DummyUser())

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


# Test de CSV_validator


def test_csv_valid():
    csv = """id,name,brand,style,alcohol,ibu,origin
1,Beer A,BrandX,Lager,5.2,20,Germany
2,Beer B,BrandY,IPA,6.0,45,USA
"""
    csv_correcto, error = validate_csv_content(csv)
    assert csv_correcto is True
    assert error is None


def test_csv_empty():
    csv = ""
    csv_correcto, error = validate_csv_content(csv)
    assert csv_correcto is False
    assert error["message"] == "CSV file is empty"


# Esto lo añade automaticamente si el csv lo creas desde excel, notepad, etc
def test_csv_with_bom():
    csv = "\ufeffid,name,brand,style,alcohol,ibu,origin\n1,A,B,C,5.0,10,D"
    csv_correcto, error = validate_csv_content(csv)
    assert csv_correcto is True


def test_csv_invalid_header():
    csv = """idx,pacopepe,pruebaneitor,style,alcohol,ibu,origin
1,cerveza A,marcaX,Lager,5.2,20,Germany
"""
    csv_correcto, error = validate_csv_content(csv)
    assert csv_correcto is False
    assert error["message"] == "Invalid CSV header"
    assert error["expected"] == ["id", "name", "brand", "style", "alcohol", "ibu", "origin"]


def test_csv_wrong_column_count():
    csv = """id,name,brand,style,alcohol,ibu,origin
1,cerveza A
"""
    csv_correcto, error = validate_csv_content(csv)
    assert csv_correcto is False
    assert "Row 2 has" in error["error"]


def test_csv_invalid_alcohol_not_number():
    csv = """id,name,brand,style,alcohol,ibu,origin
1,cerveza A,marcaX,Lager,eres-alcoholico,20,Germany
"""
    csv_correcto, error = validate_csv_content(csv)
    assert csv_correcto is False
    assert error["message"] == "Alcohol must be a decimal number in row 2"


def test_csv_invalid_alcohol_range():
    csv = """id,name,brand,style,alcohol,ibu,origin
1,Beer A,BrandX,Lager,150,20,Germany
"""
    csv_correcto, error = validate_csv_content(csv)
    assert csv_correcto is False
    assert "Invalid alcohol value" in error["message"]


def test_csv_invalid_ibu_not_int():
    csv = """id,name,brand,style,alcohol,ibu,origin
1,Beer A,BrandX,Lager,5.0,notint,Germany
"""
    csv_correcto, error = validate_csv_content(csv)
    assert csv_correcto is False
    assert error["message"] == "IBU must be an integer in row 2"


def test_csv_invalid_ibu_range():
    csv = """id,name,brand,style,alcohol,ibu,origin
1,Beer A,BrandX,Lager,5.0,500,Germany
"""
    csv_correcto, error = validate_csv_content(csv)
    assert csv_correcto is False
    assert "Invalid IBU value" in error["message"]


# Test unitarios de las rutas del validator


def test_validate_file_success(client, monkeypatch):

    def fake_validator(content):
        assert content == "test-csv"
        return True, None

    monkeypatch.setattr(dataset_routes, "validate_csv_content", fake_validator)

    response = client.post("/dataset/file/validate", json={"content": "test-csv"})

    data = response.get_json()

    assert response.status_code == 200
    assert data["valid"] is True


def test_validate_file_error(client, monkeypatch):

    def fake_validator(content):
        return False, {"message": "Mock error", "row": 3}

    monkeypatch.setattr(dataset_routes, "validate_csv_content", fake_validator)

    response = client.post("/dataset/file/validate", json={"content": "bad-csv"})

    data = response.get_json()

    assert response.status_code == 200
    assert data["valid"] is False
    assert data["error"]["message"] == "Mock error"
    assert data["error"]["row"] == 3


# Test de upload files que como ahora son csv hay que probarlos


def test_upload_success(client, monkeypatch):
    """Debe aceptar un CSV válido, guardarlo y devolver 200."""

    # Mock del validador
    def fake_validator(content):
        assert "col1,col2" in content
        return True, None

    monkeypatch.setattr(dataset_routes, "validate_csv_content", fake_validator)

    # Mock de sistema de archivos
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    monkeypatch.setattr(os, "makedirs", lambda path: None)

    saved_path = {}

    # Mock de FileStorage.save (el REAL que Flask usa)
    def fake_filestorage_save(self, dst, *args, **kwargs):
        saved_path["path"] = dst

    monkeypatch.setattr(FileStorage, "save", fake_filestorage_save)

    # Archivo que Flask procesará como FileStorage real
    file_data = (BytesIO(b"col1,col2\n1,2"), "test.csv")

    response = client.post(
        "/dataset/file/upload",
        data={"file": file_data},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    data = response.get_json()

    assert data["message"] == "CSV uploaded and validated successfully"
    assert data["filename"] == "test.csv"

    # Confirmar que el archivo fue "guardado"
    assert saved_path["path"].endswith("test.csv")


def test_upload_invalid_csv(client, monkeypatch):
    """Debe devolver 400 si validate_csv_content indica error."""

    def fake_validator(content):
        return False, {"message": "Invalid CSV", "row": 2}

    monkeypatch.setattr(dataset_routes, "validate_csv_content", fake_validator)

    file_data = BytesIO(b"bad csv data")
    file_data.filename = "invalid.csv"

    data = {"file": (file_data, "invalid.csv")}

    resp = client.post(
        "/dataset/file/upload",
        data=data,
        content_type="multipart/form-data",
    )

    assert resp.status_code == 400
    assert resp.get_json()["message"] == "Invalid CSV"
