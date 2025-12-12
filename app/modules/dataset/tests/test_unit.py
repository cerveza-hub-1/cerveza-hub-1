import os
import pandas as pd
import numpy as np
from io import BytesIO
from unittest.mock import MagicMock, patch
from scipy.sparse import csr_matrix

import pytest
from werkzeug.datastructures import FileStorage

import app.modules.dataset.routes as dataset_routes
from app import create_app
from app.modules.dataset.csv_validator import validate_csv_content
from app.modules.dataset.services import DataSetService, RecommendationEngine


class MockAuthor:
    def __init__(self, name, affiliation):
        self.name = name
        self.affiliation = affiliation

class MockPublicationType:
    def __init__(self, value):
        self.value = value

class MockDSMetaData:
    def __init__(self, title, desc, tags, authors, publication_type_value="Journal"):
        self.title = title
        self.description = desc
        self.tags = tags
        self.authors = authors
        self.dataset_doi = f"doi-{title}"
        self.publication_type = MockPublicationType(publication_type_value)


class MockDataSet:
    def __init__(self, id, metadata):
        self.id = id
        self.ds_meta_data = metadata


@pytest.fixture
def client(monkeypatch):
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

    monkeypatch.setattr("flask_login.utils._get_user", lambda: DummyUser())

    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_app():
    return MagicMock()


@pytest.fixture
def sample_datasets():
    d1 = MockDataSet(
        1,
        MockDSMetaData(
            "Title A", "Desc A", "tag1, tag2", [MockAuthor("Auth A", "Univ A")]
        )
    )
    d2 = MockDataSet(
        2,
        MockDSMetaData(
            "Title B", "Desc B", "tag2, tag3", [MockAuthor("Auth B", "Univ B")]
        )
    )
    return [d1, d2]

@pytest.fixture
def flask_app():
    app = create_app()
    app.testing = True
    with app.app_context():
        yield app

def test_get_most_downloaded_datasets_success(client, monkeypatch):
    sample = [{"id": 1, "title": "Dataset A", "downloads": 10}, {"id": 2, "title": "Dataset B", "downloads": 5}]

    class StubService:
        def get_most_downloaded_datasets(self, limit=5):
            return sample

    monkeypatch.setattr(dataset_routes, "dataset_service", StubService())
    resp = client.get("/dataset/ranking/downloads")
    assert resp.status_code == 200
    assert resp.get_json() == sample


def test_get_most_viewed_datasets_success(client, monkeypatch):
    sample = [{"id": 3, "title": "Dataset C", "views": 20}, {"id": 4, "title": "Dataset D", "views": 7}]

    class StubService:
        def get_most_viewed_datasets(self, limit=5):
            return sample

    monkeypatch.setattr(dataset_routes, "dataset_service", StubService())
    resp = client.get("/dataset/ranking/views")
    assert resp.status_code == 200
    assert resp.get_json() == sample


# --- Tests CSV Validator ---
def test_csv_valid():
    csv = "id,name,brand,style,alcohol,ibu,origin\n1,Beer A,BrandX,Lager,5.2,20,Germany\n2,Beer B,BrandY,IPA,6.0,45,USA\n"
    valid, err = validate_csv_content(csv)
    assert valid is True
    assert err is None


def test_csv_empty():
    valid, err = validate_csv_content("")
    assert valid is False
    assert err["message"] == "CSV file is empty"


# --- Recommendation Engine Tests ---
class TestRecommendationEngine:

    @patch("app.modules.dataset.services.DataSet")
    @patch("app.modules.dataset.services.nlp_utils")
    @patch("app.modules.dataset.services.create_in")
    @patch("app.modules.dataset.services.os.makedirs")
    @patch("app.modules.dataset.services.shutil.rmtree")
    def test_initialization_and_training(
        self, mock_rmtree, mock_makedirs, mock_create_in, mock_nlp, mock_dataset_model, flask_app, sample_datasets
    ):
        mock_dataset_model.query.all.return_value = sample_datasets
        mock_nlp.proceso_contenido_completo.side_effect = lambda x: f"processed_{x[:10]}"

        engine = RecommendationEngine(flask_app)

        assert not engine.df.empty
        assert len(engine.df) == 2
        assert "full_text_corpus" in engine.df.columns
        assert "full_text_corpus" in engine.models
        assert engine.models["full_text_corpus"]["vectorizer"] is not None

    @patch("app.modules.dataset.services.DataSet")
    def test_initialization_empty_db(self, mock_dataset_model, flask_app):
        mock_dataset_model.query.all.return_value = []

        engine = RecommendationEngine(flask_app)

        assert engine.df.empty
        assert engine.models == {}

    @patch("app.modules.dataset.services.DataSet")
    def test_get_similar_datasets_logic(self, mock_dataset_model, flask_app):
        mock_dataset_model.query.all.return_value = []

        service = DataSetService()
        engine = RecommendationEngine(flask_app)

        # Datos simulados
        engine.df = pd.DataFrame([
            {"dataset_id": 101, "title": "Java Project", "dataset_doi": "doi/1"},
            {"dataset_id": 102, "title": "Python Project", "dataset_doi": "doi/2"},
            {"dataset_id": 103, "title": "Java Advanced", "dataset_doi": "doi/3"},
        ])
        fake_matrix = csr_matrix([[1.0, 0.0], [0.0, 1.0], [0.9, 0.1]])
        engine.models = {"full_text_corpus": {"vectorizer": MagicMock(), "matrix": fake_matrix}}
        DataSetService._recommendation_engine = engine

        recs = service.get_similar_datasets(target_dataset_id=101, top_n=5)
        assert len(recs) == 2
        assert recs[0]["dataset_id"] == 103
        assert recs[0]["similarity_score"] > 0.8
        assert recs[1]["dataset_id"] == 102
        assert recs[1]["similarity_score"] < 0.2

    @patch("app.modules.dataset.services.DataSet")
    def test_get_similar_datasets_not_found(self, mock_dataset_model, flask_app):
        mock_dataset_model.query.all.return_value = []
        service = DataSetService()
        engine = RecommendationEngine(flask_app)
        engine.df = pd.DataFrame([{"dataset_id": 1}])
        engine.models = {"full_text_corpus": {"matrix": np.array([[1]])}}
        DataSetService._recommendation_engine = engine

        recs = service.get_similar_datasets(target_dataset_id=999)
        assert recs == []

    @patch("app.modules.dataset.services.DataSet")
    @patch("app.modules.dataset.services.nlp_utils")
    def test_force_retrain(self, mock_nlp, mock_dataset_model, flask_app):
        mock_dataset_model.query.all.return_value = []
        engine = RecommendationEngine(flask_app)
        with patch.object(engine, "_initialize_engine") as mock_init:
            engine.force_retrain()
            mock_init.assert_called_once()

    def test_get_similar_datasets_no_model(self, flask_app):
        service = DataSetService()
        engine = RecommendationEngine(flask_app)
        engine.df = pd.DataFrame([{"dataset_id": 1, "title": "X", "dataset_doi": "d1"}])
        engine.models = {}
        DataSetService._recommendation_engine = engine
        out = service.get_similar_datasets(1)
        assert out == []

    def test_get_similar_datasets_missing_row(self, flask_app):
        service = DataSetService()
        engine = RecommendationEngine(flask_app)
        engine.df = pd.DataFrame([{"dataset_id": 2, "title": "X", "dataset_doi": "d2"}])
        engine.models = {"full_text_corpus": {"matrix": np.array([[1]])}}
        DataSetService._recommendation_engine = engine
        out = service.get_similar_datasets(1)
        assert out == []
    

    @patch("app.modules.dataset.services.DataSet")
    @patch("app.modules.dataset.services.nlp_utils")
    def test_initialization_with_none_publication_type(self, mock_nlp, mock_dataset_model, flask_app):
        # Dataset con publication_type None
        class MockMeta:
            def __init__(self):
                self.title = "T"
                self.description = "D"
                self.tags = "tag"
                self.authors = [MockAuthor("A", "U")]
                self.dataset_doi = "doi-T"
                self.publication_type = None  

        d = MockDataSet(1, MockMeta())
        mock_dataset_model.query.all.return_value = [d]
        mock_nlp.proceso_contenido_completo.side_effect = lambda x: x

        engine = RecommendationEngine(flask_app)
        assert "full_text_corpus" in engine.df.columns

    @patch("app.modules.dataset.services.DataSet")
    def test_force_retrain_calls_initialize(self, mock_dataset_model, flask_app):
        # Verifica que force_retrain llame a _initialize_engine
        mock_dataset_model.query.all.return_value = []
        engine = RecommendationEngine(flask_app)
        with patch.object(engine, "_initialize_engine") as mock_init:
            engine.force_retrain()
            mock_init.assert_called_once()

    @patch("app.modules.dataset.services.DataSet")
    @patch("app.modules.dataset.services.nlp_utils")
    def test_get_corpus_data_handles_empty_dataset_list(self, mock_nlp, mock_dataset_model, flask_app):
        mock_dataset_model.query.all.return_value = []
        mock_nlp.proceso_contenido_completo.side_effect = lambda x: x
        engine = RecommendationEngine(flask_app)
        # Debe generar df vacío y no lanzar excepción
        assert engine.df.empty


