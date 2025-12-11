

import pytest

from app import create_app, db
from app.modules.auth.models import User
from app.modules.csvmodel.models import CSVModel, FMMetaData
from app.modules.dataset.models import Author, DataSet, DSMetaData, DSMetrics, PublicationType


@pytest.fixture
def client(tmp_path):
    # Crear aplicación
    app = create_app("testing")
    app.testing = True

    # ⚠️ Sobrescribir base de datos ANTES del app_context
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path}/test.db"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}

    with app.app_context():
        # Crear tablas para SQLite
        db.drop_all()
        db.create_all()

        with app.test_client() as client:
            yield client


@pytest.fixture
def build_dataset():

    def _build(
        title="Dataset A",
        description="Description A",
        authors=None,
        tags="tag1,tag2",
        publication_type=PublicationType.OTHER,
        dataset_doi="10.1234/doi",
        csv_filename="file.csv",
        csv_title="CSV Title",
        csv_tags="csv,tag",
        publication_doi="pub-doi",
        affiliation=None,
        orcid=None,
    ):

        # Usuario válido
        user = User.query.first()
        if not user:
            user = User(email="test@example.com", password="1234")
            db.session.add(user)
            db.session.flush()

        ds_metrics = DSMetrics(number_of_models="1", number_of_csv="1")
        db.session.add(ds_metrics)
        db.session.flush()

        meta = DSMetaData(
            title=title,
            description=description,
            publication_type=publication_type,
            publication_doi=publication_doi,
            dataset_doi=dataset_doi,
            tags=tags,
            ds_metrics=ds_metrics,
        )
        db.session.add(meta)
        db.session.flush()

        if not authors:
            authors = ["John Tester"]

        for a in authors:
            db.session.add(
                Author(
                    name=a,
                    affiliation=affiliation,
                    orcid=orcid,
                    ds_meta_data_id=meta.id,
                )
            )

        dataset = DataSet(user_id=user.id, ds_meta_data_id=meta.id)
        db.session.add(dataset)
        db.session.flush()

        fm_meta = FMMetaData(
            csv_filename=csv_filename,
            title=csv_title,
            description="CSV Desc",
            publication_type=publication_type,
            publication_doi=publication_doi,
            tags=csv_tags,
        )
        db.session.add(fm_meta)
        db.session.flush()

        csv_model = CSVModel(
            data_set_id=dataset.id,
            fm_meta_data_id=fm_meta.id,
        )
        db.session.add(csv_model)
        db.session.commit()

        return dataset

    return _build


def test_explore_get(client):
    response = client.get("/explore")

    assert response.status_code == 200
    assert b"<form" in response.data


def test_integration_explore_post_returns_results(client, clean_database, build_dataset):
    ds = build_dataset(title="Spanish Beer Study")

    response = client.post("/explore", json={"query": "beer"})

    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 1
    assert data[0]["id"] == ds.id


def test_explore_post_empty_results(client, clean_database, build_dataset):
    build_dataset(title="Car Dataset")

    response = client.post("/explore", json={"query": "beer"})

    assert response.status_code == 200
    assert response.get_json() == []
