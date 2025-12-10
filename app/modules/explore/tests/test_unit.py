from datetime import datetime

import pytest

import app.modules.explore.routes as explore_routes
from app import create_app, db
from app.modules.auth.models import User
from app.modules.csvmodel.models import CSVModel, FMMetaData
from app.modules.dataset.models import Author, DataSet, DSMetaData, DSMetrics, PublicationType
from app.modules.explore.repositories import ExploreRepository


@pytest.fixture
def client():
    app = create_app("testing")
    app.testing = True
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

        # Asegurar usuario válido
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


@pytest.fixture
def repo():
    return ExploreRepository()


# --------------------------------------------------------------------------------------
# PROBANDO REPOSITORIO DE EXPLORE
# ----------------------------------------------------------------------------------


def test_filter_with_no_query(clean_database, build_dataset, repo):
    # me deberia devolver soloa quellos dataset con doi
    ds1 = build_dataset(dataset_doi="10.000/abc")
    ds2 = build_dataset(dataset_doi=None)
    results = repo.filter()

    assert len(results) == 1
    assert results[0].id == ds1.id


def test_filter_by_titulo(clean_database, build_dataset, repo):
    target = build_dataset(title="Super Beer Dataset")
    build_dataset(title="Another dataset")

    results = repo.filter(query="super beer")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_by_description(clean_database, build_dataset, repo):
    target = build_dataset(description="Contains beer information")
    build_dataset(description="Irrelevant")

    results = repo.filter(description="beer")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_by_author_single(clean_database, build_dataset, repo):
    target = build_dataset(authors=["Alice"])
    build_dataset(authors=["Bob"])

    results = repo.filter(authors="Alice")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_by_multiple_authors(clean_database, build_dataset, repo):
    target = build_dataset(authors=["Alice", "Bob"])
    build_dataset(authors=["Alice"])
    build_dataset(authors=["Bob"])

    results = repo.filter(authors="Alice;Bob")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_by_affiliation(clean_database, build_dataset, repo):
    target = build_dataset(authors=["Alice"], affiliation="MIT")
    build_dataset(authors=["Bob"], affiliation="Stanford")

    results = repo.filter(affiliation="MIT")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_by_orcid(clean_database, build_dataset, repo):
    target = build_dataset(authors=["Alice"], orcid="0000-000X")
    build_dataset(authors=["Bob"], orcid="1111-2222")

    results = repo.filter(orcid="0000")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_by_csv_filename(clean_database, build_dataset, repo):
    target = build_dataset(csv_filename="beer_data.csv")
    build_dataset(csv_filename="other.csv")

    results = repo.filter(csv_filename="beer_data")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_by_publication_doi(clean_database, build_dataset, repo):
    target = build_dataset(publication_doi="10.aaa/bbb")
    build_dataset(publication_doi="foo")

    results = repo.filter(publication_doi="aaa")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_by_tags(clean_database, build_dataset, repo):
    target = build_dataset(tags="beer,stats", csv_tags="other")
    build_dataset(tags="wine", csv_tags="none")

    results = repo.filter(tags="beer")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_sorting(clean_database, build_dataset, repo):
    ds1 = build_dataset(title="Oldest")
    ds2 = build_dataset(title="Newest")

    ds1.created_at = datetime(2020, 1, 1)
    ds2.created_at = datetime(2024, 1, 1)
    db.session.commit()

    newest = repo.filter(sorting="newest")
    oldest = repo.filter(sorting="oldest")

    assert newest[0].id == ds2.id
    assert oldest[0].id == ds1.id


from datetime import datetime

import pytest

from app import db
from app.modules.auth.models import User
from app.modules.csvmodel.models import CSVModel, FMMetaData
from app.modules.dataset.models import Author, DataSet, DSMetaData, DSMetrics, PublicationType
from app.modules.explore.repositories import ExploreRepository


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

        # Asegurar usuario válido
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


@pytest.fixture
def repo():
    return ExploreRepository()


# --------------------------------------------------------------------------------------
# PROBANDO REPOSITORIO DE EXPLORE
# ----------------------------------------------------------------------------------


def test_filter_with_no_query(clean_database, build_dataset, repo):
    # me deberia devolver soloa quellos dataset con doi
    ds1 = build_dataset(dataset_doi="10.000/abc")
    ds2 = build_dataset(dataset_doi=None)
    results = repo.filter()

    assert len(results) == 1
    assert results[0].id == ds1.id


def test_filter_by_titulo(clean_database, build_dataset, repo):
    target = build_dataset(title="Super Beer Dataset")
    build_dataset(title="Another dataset")

    results = repo.filter(query="super beer")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_by_description(clean_database, build_dataset, repo):
    target = build_dataset(description="Contains beer information")
    build_dataset(description="Irrelevant")

    results = repo.filter(description="beer")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_by_author_single(clean_database, build_dataset, repo):
    target = build_dataset(authors=["Alice"])
    build_dataset(authors=["Bob"])

    results = repo.filter(authors="Alice")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_by_multiple_authors(clean_database, build_dataset, repo):
    target = build_dataset(authors=["Alice", "Bob"])
    build_dataset(authors=["Alice"])
    build_dataset(authors=["Bob"])

    results = repo.filter(authors="Alice;Bob")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_by_affiliation(clean_database, build_dataset, repo):
    target = build_dataset(authors=["Alice"], affiliation="MIT")
    build_dataset(authors=["Bob"], affiliation="Stanford")

    results = repo.filter(affiliation="MIT")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_by_orcid(clean_database, build_dataset, repo):
    target = build_dataset(authors=["Alice"], orcid="0000-000X")
    build_dataset(authors=["Bob"], orcid="1111-2222")

    results = repo.filter(orcid="0000")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_by_csv_filename(clean_database, build_dataset, repo):
    target = build_dataset(csv_filename="beer_data.csv")
    build_dataset(csv_filename="other.csv")

    results = repo.filter(csv_filename="beer_data")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_by_publication_doi(clean_database, build_dataset, repo):
    target = build_dataset(publication_doi="10.aaa/bbb")
    build_dataset(publication_doi="foo")

    results = repo.filter(publication_doi="aaa")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_by_tags(clean_database, build_dataset, repo):
    target = build_dataset(tags="beer,stats", csv_tags="other")
    build_dataset(tags="wine", csv_tags="none")

    results = repo.filter(tags="beer")

    assert len(results) == 1
    assert results[0].id == target.id


def test_filter_sorting(clean_database, build_dataset, repo):
    ds1 = build_dataset(title="Oldest")
    ds2 = build_dataset(title="Newest")

    ds1.created_at = datetime(2020, 1, 1)
    ds2.created_at = datetime(2024, 1, 1)
    db.session.commit()

    newest = repo.filter(sorting="newest")
    oldest = repo.filter(sorting="oldest")

    assert newest[0].id == ds2.id
    assert oldest[0].id == ds1.id


def test_explore_get(client):
    response = client.get("/explore")

    assert response.status_code == 200
    assert b"<form" in response.data


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


def test_explore_post_failure(client, monkeypatch):

    def fake_filter_error(**criteria):
        raise RuntimeError("Service failure")

    monkeypatch.setattr(explore_routes.ExploreService, "filter", staticmethod(fake_filter_error))

    response = client.post("/explore", json={"query": "siu"})

    assert response.status_code == 500


def test_explore_get_failure(client, monkeypatch):

    def fake_render_template(*args, **kwargs):
        raise RuntimeError("Template rendering error")

    monkeypatch.setattr(explore_routes, "render_template", fake_render_template)

    response = client.get("/explore")

    assert response.status_code == 500
