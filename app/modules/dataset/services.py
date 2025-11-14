import hashlib
import logging
import os
import shutil
import tempfile
import uuid
from typing import Dict, List, Optional

import pandas as pd
from flask import request
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import ID, TEXT, Schema
from whoosh.index import create_in

from app.modules.auth.services import AuthenticationService
from app.modules.dataset import nlp_utils
from app.modules.dataset.models import DataSet, DSMetaData, DSViewRecord
from app.modules.dataset.repositories import (
    AuthorRepository,
    DataSetRepository,
    DOIMappingRepository,
    DSDownloadRecordRepository,
    DSMetaDataRepository,
    DSViewRecordRepository,
)
from app.modules.featuremodel.repositories import (
    FeatureModelRepository,
    FMMetaDataRepository,
)
from app.modules.hubfile.repositories import (
    HubfileDownloadRecordRepository,
    HubfileRepository,
    HubfileViewRecordRepository,
)
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)

CorpusRecord = Dict[str, any]

INDEXABLE_FIELDS = ["authors", "tags", "affiliation"]


class RecommendationEngine:
    """Clase interna para manejar la lógica de PLN y TF-IDF.
    Se inicializa solo una vez por la aplicación (singleton)."""

    def __init__(self, app_instance):
        self.app = app_instance
        self.df = pd.DataFrame()
        self.models = {}
        self.whoosh_indices = {}
        self.tfidf_matrix = None
        self.tfidf_vectorizer = None
        self._initialize_engine()
        logger.info("RecommendationEngine initialized.")

    def _get_corpus_data_from_db(self) -> List[CorpusRecord]:
        """Extrae los metadatos de los DataSets que son relevantes para la similitud."""

        corpus_data: List[CorpusRecord] = []
        logger.debug("--- INICIO: Extracción de corpus de la Base de Datos ---")

        with self.app.app_context():

            datasets = DataSet.query.all()

            if not datasets:
                logger.warning("No se encontraron DataSets en la base de datos.")
                return []

            for ds in datasets:
                metadata: DSMetaData = ds.ds_meta_data

                authors_names = []
                affiliation_names = []
                for author in metadata.authors:
                    authors_names.append(author.name.lower())
                    if author.affiliation:
                        affiliation_names.append(author.affiliation.lower())

                tags_list = [tag.strip().lower() for tag in metadata.tags.split(",") if metadata.tags]

                text_components_raw = [
                    metadata.title,
                    metadata.description,
                    metadata.publication_type.value,
                    " ".join(authors_names),
                    " ".join(affiliation_names),
                    " ".join(tags_list),
                ]

                raw_combined_text = " ".join(filter(None, text_components_raw))

                full_text_processed = nlp_utils.proceso_contenido_completo(raw_combined_text)

                corpus_data.append(
                    {
                        "dataset_id": ds.id,
                        "title": metadata.title,
                        "description": metadata.description,
                        "authors": " ".join(authors_names),
                        "affiliation": " ".join(affiliation_names),
                        "tags": " ".join(tags_list),
                        "dataset_doi": metadata.dataset_doi,
                        "full_text_corpus": full_text_processed,
                    }
                )

        logger.info(f"Corpus extraction complete. {len(corpus_data)} records retrieved.")
        return corpus_data

    def _create_whoosh_index(self, field_name: str):
        """Crea un índice Whoosh temporal para un campo específico."""

        index_dir = os.path.join(tempfile.gettempdir(), f"whoosh_index_{field_name}")

        if os.path.exists(index_dir):
            shutil.rmtree(index_dir)

        os.makedirs(index_dir, exist_ok=True)

        schema = Schema(doc_id=ID(stored=True, unique=True), content=TEXT(stored=True, analyzer=StemmingAnalyzer()))

        ix = create_in(index_dir, schema)
        writer = ix.writer()

        for i, text in enumerate(self.df[field_name].tolist()):
            dataset_id = str(self.df.iloc[i]["dataset_id"])
            writer.add_document(doc_id=dataset_id, content=text)

        writer.commit()
        return ix

    def _train_and_index_models(self):
        """Entrena modelos TF-IDF para el corpus completo y crea índices Whoosh para campos específicos."""

        if self.df.empty or "full_text_corpus" not in self.df.columns:
            logger.warning("DataFrame está vacío o falta 'full_text_corpus'. Saltando entrenamiento.")
            return

        vectorizer = TfidfVectorizer(tokenizer=lambda x: x.split(), preprocessor=lambda x: x, stop_words=None)
        matrix = vectorizer.fit_transform(self.df["full_text_corpus"])

        self.models["full_text_corpus"] = {"vectorizer": vectorizer, "matrix": matrix}

        for field in INDEXABLE_FIELDS:
            field_vectorizer = TfidfVectorizer(token_pattern=r"\b\w+\b")
            field_matrix = field_vectorizer.fit_transform(self.df[field])

            self.models[field] = {"vectorizer": field_vectorizer, "matrix": field_matrix}

            whoosh_ix = self._create_whoosh_index(field)
            self.whoosh_indices[field] = whoosh_ix

        logger.info("TF-IDF models trained for fields: %s.", list(self.models.keys()))
        logger.info("Whoosh indices created for fields: %s.", list(self.whoosh_indices.keys()))

    def _initialize_engine(self):
        """Carga los datos y entrena el modelo."""
        corpus = self._get_corpus_data_from_db()
        if corpus:
            self.df = pd.DataFrame(corpus)
            self._train_and_index_models()

    def force_retrain(self):
        """
        Forza un re-entrenamiento completo del motor de recomendación.
        Esto recarga todos los datasets de la base de datos.
        """
        self._initialize_engine()


def calculate_checksum_and_size(file_path):
    """Calcula el checksum MD5 y el tamaño de un archivo."""
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as file:
        content = file.read()
        hash_md5 = hashlib.md5(content).hexdigest()
        return hash_md5, file_size


class DataSetService(BaseService):
    """
    Servicio para gestionar la lógica de negocio de los DataSets.
    Incluye la inicialización perezosa del motor de recomendación.
    """

    _recommendation_engine: Optional["RecommendationEngine"] = None

    def __init__(self):
        super().__init__(DataSetRepository())
        self.feature_model_repository = FeatureModelRepository()
        self.author_repository = AuthorRepository()
        self.dsmetadata_repository = DSMetaDataRepository()
        self.fmmetadata_repository = FMMetaDataRepository()
        self.dsdownloadrecord_repository = DSDownloadRecordRepository()
        self.hubfiledownloadrecord_repository = HubfileDownloadRecordRepository()
        self.hubfilerepository = HubfileRepository()
        self.dsviewrecord_repostory = DSViewRecordRepository()
        self.hubfileviewrecord_repository = HubfileViewRecordRepository()

    def _get_or_create_engine(self) -> "RecommendationEngine":
        """
        Cargador perezoso (Lazy loader) para el singleton del RecommendationEngine.
        Esto evita la importación circular durante el inicio de la app.
        """
        if DataSetService._recommendation_engine is None:
            from app import app as flask_app_instance

            logger.info("Inicializando RecommendationEngine (singleton)...")
            DataSetService._recommendation_engine = RecommendationEngine(flask_app_instance)
        return DataSetService._recommendation_engine

    def get_similar_datasets(
        self, target_dataset_id: int, field_type: str = "full_text_corpus", top_n: int = 5
    ) -> List[Dict]:
        """
        Calcula y devuelve los N datasets más similares al dataset target
        basándose en el tipo de campo especificado ('authors', 'tags', 'affiliation', o 'full_text_corpus').
        """

        top_n = 5

        engine = self._get_or_create_engine()

        valid_fields = list(engine.models.keys())
        if field_type not in valid_fields:
            logger.warning(f"Field type '{field_type}' not found in models. Using default: 'full_text_corpus'.")
            field_type = "full_text_corpus"

        model = engine.models.get(field_type)
        df = engine.df

        if df.empty or model is None:
            logger.warning("Motor de recomendación no entrenado o DataFrame vacío. Devolviendo [].")
            return []

        try:
            target_index = df.index[df["dataset_id"] == target_dataset_id].tolist()
        except KeyError:
            logger.error("Columna 'dataset_id' no encontrada en el DataFrame del motor.")
            return []

        if not target_index:
            logger.warning(f"Dataset ID {target_dataset_id} no encontrado en el motor. Devolviendo [].")
            return []

        target_idx = target_index[0]

        cosine_sim = cosine_similarity(model["matrix"][target_idx], model["matrix"]).flatten()

        similar_indices = cosine_sim.argsort()[: -top_n - 1 : -1]

        recommendations = []
        for i in similar_indices:
            if i == target_idx:
                continue

            recommendations.append(
                {
                    "dataset_id": df.iloc[i]["dataset_id"],
                    "title": df.iloc[i]["title"],
                    "similarity_score": round(cosine_sim[i], 4),
                    "dataset_doi": df.iloc[i]["dataset_doi"],
                }
            )

        return recommendations

    def move_feature_models(self, dataset: DataSet):
        """Mueve los modelos de características de la carpeta temporal al directorio permanente."""
        current_user = AuthenticationService().get_authenticated_user()
        source_dir = current_user.temp_folder()

        working_dir = os.getenv("WORKING_DIR", "")
        dest_dir = os.path.join(working_dir, "uploads", f"user_{current_user.id}", f"dataset_{dataset.id}")

        os.makedirs(dest_dir, exist_ok=True)

        for feature_model in dataset.feature_models:
            uvl_filename = feature_model.fm_meta_data.uvl_filename
            shutil.move(os.path.join(source_dir, uvl_filename), dest_dir)

    def get_synchronized(self, current_user_id: int) -> DataSet:
        """Obtiene datasets sincronizados para un usuario."""
        return self.repository.get_synchronized(current_user_id)

    def get_unsynchronized(self, current_user_id: int) -> DataSet:
        """Obtiene datasets no sincronizados para un usuario."""
        return self.repository.get_unsynchronized(current_user_id)

    def get_unsynchronized_dataset(self, current_user_id: int, dataset_id: int) -> DataSet:
        """Obtiene un dataset no sincronizado específico."""
        return self.repository.get_unsynchronized_dataset(current_user_id, dataset_id)

    def latest_synchronized(self):
        """Obtiene los últimos datasets sincronizados."""
        return self.repository.latest_synchronized()

    def count_synchronized_datasets(self):
        """Cuenta los datasets sincronizados."""
        return self.repository.count_synchronized_datasets()

    def count_feature_models(self):
        """Cuenta el total de modelos de características."""
        return self.feature_model_repository.count()

    def count_authors(self) -> int:
        """Cuenta el total de autores."""
        return self.author_repository.count()

    def count_dsmetadata(self) -> int:
        """Cuenta el total de metadatos de datasets."""
        return self.dsmetadata_repository.count()

    def total_dataset_downloads(self) -> int:
        """Obtiene el total de descargas de datasets."""
        return self.dsdownloadrecord_repository.total_dataset_downloads()

    def total_dataset_views(self) -> int:
        """Obtiene el total de vistas de datasets."""
        return self.dsviewrecord_repostory.total_dataset_views()

    def create_from_form(self, form, current_user) -> DataSet:
        """Crea un nuevo DataSet a partir de un formulario y el usuario actual."""
        main_author = {
            "name": f"{current_user.profile.surname}, {current_user.profile.name}",
            "affiliation": current_user.profile.affiliation,
            "orcid": current_user.profile.orcid,
        }
        try:
            logger.info("Creating dsmetadata...: %s", form.get_dsmetadata())
            dsmetadata = self.dsmetadata_repository.create(**form.get_dsmetadata())
            for author_data in [main_author] + form.get_authors():
                author = self.author_repository.create(commit=False, ds_meta_data_id=dsmetadata.id, **author_data)
                dsmetadata.authors.append(author)

            dataset = self.create(commit=False, user_id=current_user.id, ds_meta_data_id=dsmetadata.id)

            for feature_model in form.feature_models:
                uvl_filename = feature_model.uvl_filename.data
                fmmetadata = self.fmmetadata_repository.create(commit=False, **feature_model.get_fmmetadata())
                for author_data in feature_model.get_authors():
                    author = self.author_repository.create(commit=False, fm_meta_data_id=fmmetadata.id, **author_data)
                    fmmetadata.authors.append(author)

                fm = self.feature_model_repository.create(
                    commit=False, data_set_id=dataset.id, fm_meta_data_id=fmmetadata.id
                )

                # associated files in feature model
                file_path = os.path.join(current_user.temp_folder(), uvl_filename)
                checksum, size = calculate_checksum_and_size(file_path)

                file = self.hubfilerepository.create(
                    commit=False, name=uvl_filename, checksum=checksum, size=size, feature_model_id=fm.id
                )
                fm.files.append(file)
            self.repository.session.commit()
        except Exception as exc:
            logger.info("Exception creating dataset from form...: %s", exc)
            self.repository.session.rollback()
            raise exc
        try:
            logger.info("Nuevo dataset creado. Re-entrenando el motor de recomendación...")
            engine = self._get_or_create_engine()
            engine.force_retrain()
            logger.info("Motor de recomendación re-entrenado.")
        except Exception as e:
            # No fallar la creación del dataset si el motor falla, solo registrarlo
            logger.error(f"FALLO al re-entrenar el motor de recomendación: {e}")

        return dataset

    def update_dsmetadata(self, ds_id, **kwargs):
        """Actualiza los metadatos de un dataset."""
        return self.dsmetadata_repository.update(ds_id, **kwargs)

    def get_uvlhub_doi(self, dataset: DataSet) -> str:
        """Obtiene el DOI de UVLHub para un dataset."""
        domain = os.getenv("DOMAIN", "localhost")
        return f"http://{domain}/doi/{dataset.ds_meta_data.dataset_doi}"


class AuthorService(BaseService):
    """Servicio para la lógica de negocio de Autores."""

    def __init__(self):
        super().__init__(AuthorRepository())


class DSDownloadRecordService(BaseService):
    """Servicio para la lógica de negocio de Registros de Descarga."""

    def __init__(self):
        super().__init__(DSDownloadRecordRepository())


class DSMetaDataService(BaseService):
    """Servicio para la lógica de negocio de MetaData de DataSets."""

    def __init__(self):
        super().__init__(DSMetaDataRepository())

    def update(self, ds_id, **kwargs):
        """Actualiza metadatos."""
        return self.repository.update(ds_id, **kwargs)

    def filter_by_doi(self, doi: str) -> Optional[DSMetaData]:
        """Filtra metadatos por DOI."""
        return self.repository.filter_by_doi(doi)


class DSViewRecordService(BaseService):
    """Servicio para la lógica de negocio de Vistas de DataSets."""

    def __init__(self):
        super().__init__(DSViewRecordRepository())

    def the_record_exists(self, dataset: DataSet, user_cookie: str):
        """Verifica si ya existe un registro de vista."""
        return self.repository.the_record_exists(dataset, user_cookie)

    def create_new_record(self, dataset: DataSet, user_cookie: str) -> DSViewRecord:
        """Crea un nuevo registro de vista."""
        return self.repository.create_new_record(dataset, user_cookie)

    def create_cookie(self, dataset: DataSet) -> str:
        """Crea o recupera una cookie de vista y registra la vista si es nueva."""

        user_cookie = request.cookies.get("view_cookie")
        if not user_cookie:
            user_cookie = str(uuid.uuid4())

        existing_record = self.the_record_exists(dataset=dataset, user_cookie=user_cookie)

        if not existing_record:
            self.create_new_record(dataset=dataset, user_cookie=user_cookie)

        return user_cookie


class DOIMappingService(BaseService):
    """Servicio para la lógica de negocio de Mapeo de DOIs."""

    def __init__(self):
        super().__init__(DOIMappingRepository())

    def get_new_doi(self, old_doi: str) -> str:
        """Obtiene el nuevo DOI a partir de uno antiguo."""
        doi_mapping = self.repository.get_new_doi(old_doi)
        if doi_mapping:
            return doi_mapping.dataset_doi_new

        return None


class SizeService:
    """Servicio de utilidad para formatear tamaños de archivo."""

    def __init__(self):
        pass

    def get_human_readable_size(self, size: int) -> str:
        """Convierte bytes a un formato legible (KB, MB, GB)."""
        if size < 1024:
            return f"{size} bytes"
        if size < 1024**2:
            return f"{round(size / 1024, 2)} KB"
        if size < 1024**3:
            return f"{round(size / (1024 ** 2), 2)} MB"

        return f"{round(size / (1024 ** 3), 2)} GB"
