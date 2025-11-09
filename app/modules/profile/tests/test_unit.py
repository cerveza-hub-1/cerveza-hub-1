import pytest

from app import db
from app.modules.auth.models import User
from app.modules.conftest import login, logout
from app.modules.dataset.models import DSMetaData, DataSet, PublicationType
from app.modules.profile.models import UserProfile


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    for module testing (por example, new users)
    """
    with test_client.application.app_context():
        user_test = User(email="user@example.com", password="test1234")
        db.session.add(user_test)
        db.session.commit()

        profile = UserProfile(user_id=user_test.id, name="Name", surname="Surname")
        db.session.add(profile)
        db.session.commit()

    yield test_client


def test_edit_profile_page_get(test_client):
    """
    Tests access to the profile editing page via a GET request.
    """
    login_response = login(test_client, "user@example.com", "test1234")
    assert login_response.status_code == 200, "Login was unsuccessful."

    response = test_client.get("/profile/edit")
    assert response.status_code == 200, "The profile editing page could not be accessed."
    assert b"Edit profile" in response.data, "The expected content is not present on the page"

    logout(test_client)


def test_view_public_profile_datasets(test_client):
    """
    Verifies that a user can view another user's public profile and datasets,
    but does not see 2FA controls.
    """
    # Crar usuario y perfil de un nuevo usuario
    other_user = User(email="other@example.com", password="otherpass")
    db.session.add(other_user)
    db.session.commit()

    other_profile = UserProfile(user_id=other_user.id, name="Other", surname="User")
    db.session.add(other_profile)
    db.session.commit()

    # Crear datasets para el usuario creado
    for i in range(2):
        ds_metadata = DSMetaData(
            title=f"Dataset {i+1}",
            description="Descripción de prueba",
            publication_type=PublicationType.OTHER,
        )
        db.session.add(ds_metadata)
        db.session.commit()

        dataset = DataSet(user_id=other_user.id, ds_meta_data_id=ds_metadata.id)
        db.session.add(dataset)
    db.session.commit()

    # Usamos el usuario ya creado anteriormente
    login_response = login(test_client, "user@example.com", "test1234")
    assert login_response.status_code == 200

    response = test_client.get(f"/profile/{other_user.id}")
    assert response.status_code == 200
    assert b"Dataset 1" in response.data
    assert b"Dataset 2" in response.data
    assert b"Enable" not in response.data and b"Disable" not in response.data  # Comprobar no están controles 2FA

    logout(test_client)
