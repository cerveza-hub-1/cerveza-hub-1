import pytest

from app import create_app, db
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet, DSMetaData, DSDownloadRecord, DSViewRecord, PublicationType


@pytest.fixture(scope="function")
def test_client(tmp_path):
    """Crea la aplicación Flask en modo testing y devuelve su cliente HTTP."""
    app = create_app("testing")
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'test_dataset.db'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app.test_client(), app
        db.session.remove()


@pytest.fixture(autouse=True)
def reset_database(test_client):
    """
    Fixture que se ejecuta antes de cada test.
    Limpia todas las tablas relevantes respetando las FK y añade datos de prueba.
    """
    client, app = test_client
    with app.app_context():
        user = User(email="test@example.com", password="secret")
        db.session.add(user)
        db.session.commit()

        meta_kwargs = {
            "description": "datos de prueba",
            "publication_type": PublicationType.OTHER,
        }

        meta1 = DSMetaData(title="Dataset 1", dataset_doi="doi1", **meta_kwargs)
        meta2 = DSMetaData(title="Dataset 2", dataset_doi="doi2", **meta_kwargs)
        meta3 = DSMetaData(title="Dataset 3", dataset_doi="doi3", **meta_kwargs)
        meta4 = DSMetaData(title="Dataset 4", dataset_doi="doi4", **meta_kwargs)
        meta5 = DSMetaData(title="Dataset 5", dataset_doi="doi5", **meta_kwargs)
        meta6 = DSMetaData(title="Dataset 6", dataset_doi="doi6", **meta_kwargs)
        db.session.add_all([meta1, meta2, meta3, meta4, meta5, meta6])
        db.session.commit()

        ds1 = DataSet(user_id=user.id, ds_meta_data_id=meta1.id)
        ds2 = DataSet(user_id=user.id, ds_meta_data_id=meta2.id)
        ds3 = DataSet(user_id=user.id, ds_meta_data_id=meta3.id)
        ds4 = DataSet(user_id=user.id, ds_meta_data_id=meta4.id)
        ds5 = DataSet(user_id=user.id, ds_meta_data_id=meta5.id)
        ds6 = DataSet(user_id=user.id, ds_meta_data_id=meta6.id)
        db.session.add_all([ds1, ds2, ds3, ds4, ds5, ds6])
        db.session.commit()

        db.session.add_all(
            [
                DSViewRecord(dataset_id=ds1.id, view_cookie="v1"),
                DSViewRecord(dataset_id=ds1.id, view_cookie="v2"),
                DSViewRecord(dataset_id=ds2.id, view_cookie="v3"),
            ]
        )

        db.session.add_all(
            [
                DSDownloadRecord(dataset_id=ds2.id, download_cookie="d1"),
                DSDownloadRecord(dataset_id=ds2.id, download_cookie="d2"),
                DSDownloadRecord(dataset_id=ds3.id, download_cookie="d3"),
            ]
        )
        db.session.commit()


def test_most_viewed(test_client):
    client, _ = test_client
    response = client.get("/dataset/ranking/views")
    assert response.status_code == 200
    data = response.get_json()
    assert data[0]["title"] == "Dataset 1" and data[0]["views"] == 2
    assert data[1]["title"] == "Dataset 2" and data[1]["views"] == 1


def test_most_downloaded(test_client):
    client, _ = test_client
    response = client.get("/dataset/ranking/downloads")
    assert response.status_code == 200
    data = response.get_json()
    assert data[0]["title"] == "Dataset 2" and data[0]["downloads"] == 2
    assert data[1]["title"] == "Dataset 3" and data[1]["downloads"] == 1


def test_limiting_results_views(test_client):
    client, _ = test_client
    response = client.get("/dataset/ranking/views")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 5
    assert data[0]["title"] == "Dataset 1"
    assert data[1]["title"] == "Dataset 2"
