from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import csr_matrix

from app.modules.dataset.services import DataSetService, RecommendationEngine


# Clases Mock para simular los Modelos de la Base de Datos
class MockAuthor:
    def __init__(self, name, affiliation):
        self.name = name
        self.affiliation = affiliation


class MockDSMetaData:
    def __init__(self, title, description, tags, authors, dataset_doi="10.1234/example"):
        self.title = title
        self.description = description
        self.tags = tags
        self.authors = authors
        self.dataset_doi = dataset_doi
        self.publication_type = MagicMock()
        self.publication_type.value = "article"


class MockDataSet:
    def __init__(self, id, metadata):
        self.id = id
        self.ds_meta_data = metadata


@pytest.fixture
def mock_app():
    """Simula la instancia de la aplicación Flask."""
    app = MagicMock()
    app.app_context.return_value.__enter__.return_value = None
    app.app_context.return_value.__exit__.return_value = None
    return app


@pytest.fixture
def sample_datasets():
    """Crea una lista de datasets falsos para probar la extracción de datos."""
    d1 = MockDataSet(1, MockDSMetaData("Title A", "Desc A", "tag1, tag2", [MockAuthor("Auth A", "Univ A")]))
    d2 = MockDataSet(2, MockDSMetaData("Title B", "Desc B", "tag2, tag3", [MockAuthor("Auth B", "Univ B")]))
    return [d1, d2]


class TestRecommendationEngine:

    @patch("app.modules.dataset.services.DataSet")
    @patch("app.modules.dataset.services.nlp_utils")
    @patch("app.modules.dataset.services.create_in")
    @patch("app.modules.dataset.services.os.makedirs")
    @patch("app.modules.dataset.services.shutil.rmtree")
    def test_initialization_and_training(
        self, mock_rmtree, mock_makedirs, mock_create_in, mock_nlp, mock_dataset_model, mock_app, sample_datasets
    ):
        """Prueba inicialización y entrenamiento."""
        mock_dataset_model.query.all.return_value = sample_datasets
        mock_nlp.proceso_contenido_completo.side_effect = lambda x: f"processed_{x[:10]}"

        engine = RecommendationEngine(mock_app)

        assert not engine.df.empty
        assert len(engine.df) == 2
        assert "full_text_corpus" in engine.df.columns
        assert engine.models["full_text_corpus"]["vectorizer"] is not None

    @patch("app.modules.dataset.services.DataSet")
    def test_initialization_empty_db(self, mock_dataset_model, mock_app):
        """Prueba base de datos vacía."""
        mock_dataset_model.query.all.return_value = []
        engine = RecommendationEngine(mock_app)
        assert engine.df.empty
        assert engine.models == {}

    @patch("app.modules.dataset.services.DataSet")
    def test_get_similar_datasets_logic(self, mock_dataset_model, mock_app):
        """
        Verificación de la lógica de recomendación.
        """
        mock_dataset_model.query.all.return_value = []

        service = DataSetService()
        engine = RecommendationEngine(mock_app)

        # Datos simulados
        engine.df = pd.DataFrame(
            [
                {"dataset_id": 101, "title": "Java Project", "dataset_doi": "doi/1"},
                {"dataset_id": 102, "title": "Python Project", "dataset_doi": "doi/2"},
                {"dataset_id": 103, "title": "Java Advanced", "dataset_doi": "doi/3"},
            ]
        )

        fake_matrix = csr_matrix([[1.0, 0.0], [0.0, 1.0], [0.9, 0.1]])

        engine.models = {"full_text_corpus": {"vectorizer": MagicMock(), "matrix": fake_matrix}}

        DataSetService._recommendation_engine = engine

        # Ejecutar la prueba
        recommendations = service.get_similar_datasets(target_dataset_id=101, top_n=5)

        # Aserciones
        assert len(recommendations) == 2

        # El dataset 103 es muy similar (0.9 vs 1.0) -> Debe ser primero
        assert recommendations[0]["dataset_id"] == 103
        assert recommendations[0]["similarity_score"] > 0.8

        # El dataset 102 es ortogonal (0.0 vs 1.0) -> Debe ser segundo (o score 0)
        assert recommendations[1]["dataset_id"] == 102
        assert recommendations[1]["similarity_score"] < 0.2

    @patch("app.modules.dataset.services.DataSet")
    def test_get_similar_datasets_not_found(self, mock_dataset_model, mock_app):
        """Prueba ID no encontrado."""
        mock_dataset_model.query.all.return_value = []

        service = DataSetService()
        engine = RecommendationEngine(mock_app)

        engine.df = pd.DataFrame([{"dataset_id": 1}])
        engine.models = {"full_text_corpus": {"matrix": np.array([[1]])}}
        DataSetService._recommendation_engine = engine

        recs = service.get_similar_datasets(target_dataset_id=999)
        assert recs == []

    @patch("app.modules.dataset.services.DataSet")
    @patch("app.modules.dataset.services.nlp_utils")
    def test_force_retrain(self, mock_nlp, mock_dataset_model, mock_app):
        """Prueba reentrenamiento."""
        mock_dataset_model.query.all.return_value = []

        engine = RecommendationEngine(mock_app)

        with patch.object(engine, "_initialize_engine") as mock_init:
            engine.force_retrain()
            mock_init.assert_called_once()
