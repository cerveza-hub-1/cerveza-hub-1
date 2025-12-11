from unittest.mock import MagicMock, patch

import pyotp
import pytest
from flask import redirect, url_for

from app import db
from app.modules.auth.models import User
from app.modules.auth.services import AuthenticationService
from app.modules.conftest import login, logout
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app.modules.profile.models import UserProfile
from app.modules.profile.repositories import UserProfileRepository
from app.modules.profile.services import UserProfileService

authentication_service = AuthenticationService()


# --- Fixture del Módulo (Ajustado para asegurar la existencia) ---


@pytest.fixture(scope="module")
def test_client(test_client):
    with test_client.application.app_context():

        # 1) Crear usuario si no existe
        user_test = User.query.filter_by(email="user@example.com").first()
        if user_test is None:
            user_test = User(email="user@example.com", password="test1234")
            db.session.add(user_test)
            db.session.commit()

        # 2) Crear perfil si no existe
        profile = UserProfile.query.filter_by(user_id=user_test.id).first()
        if profile is None:
            profile = UserProfile(user_id=user_test.id, name="Name", surname="Surname")
            db.session.add(profile)
            db.session.commit()

        _ = user_test.profile

    yield test_client


# --- Funciones auxiliares para asegurar el User/Profile en tests ---
def get_fresh_user_and_profile(email="user@example.com"):
    # Recarga el usuario y su perfil en la sesión actual
    user = User.query.filter_by(email=email).first()
    if user and user.profile is None:
        raise Exception("User found but profile is missing!")
    return user, user.profile


# --- Tests para /profile/edit (Edición de Perfil) ---
def test_edit_profile_fail_no_profile_redirect(test_client, monkeypatch):
    # 1. Loguear un usuario
    login(test_client, "user@example.com", "test1234")

    with patch("app.modules.profile.routes.AuthenticationService") as MockAuthService:
        # 2. Configurar la instancia mockeada para que get_authenticated_user_profile() devuelva None
        mock_auth_service_instance = MockAuthService.return_value
        mock_auth_service_instance.get_authenticated_user_profile.return_value = None

        # 3. Intentar acceder a /profile/edit
        response = test_client.get("/profile/edit", follow_redirects=False)

    assert response.status_code == 302
    assert response.location == url_for("public.index", _external=False)

    logout(test_client)


def test_edit_profile_post_success(test_client):
    login(test_client, "user@example.com", "test1234")

    # Obtenemos el ID del perfil actual
    user, profile = get_fresh_user_and_profile()

    # 2. Mockear el servicio para simular la actualización exitosa
    with patch("app.modules.profile.routes.UserProfileService") as MockService:
        mock_service_instance = MockService.return_value

        # Simular que update_profile es exitoso
        mock_profile_updated = MagicMock(id=profile.id, name="NuevoNombre")
        mock_service_instance.update_profile.return_value = (mock_profile_updated, None)

        # Simulamos que handle_service_response devuelve la redirección esperada
        mock_service_instance.handle_service_response.return_value = redirect(url_for("profile.my_profile"))

        # 3. Enviar POST
        response = test_client.post(
            "/profile/edit",
            data={"name": "NuevoNombre", "surname": "NuevoApellido", "submit": "Save profile"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.location == url_for("profile.my_profile", _external=False)

    logout(test_client)


def test_edit_profile_post_failure(test_client):
    login(test_client, "user@example.com", "test1234")

    # 2. Mockear el servicio para simular la actualización fallida
    with patch("app.modules.profile.routes.UserProfileService") as MockService:
        mock_service_instance = MockService.return_value

        # Simular que update_profile falla (retorna None y errores)
        mock_errors = {"orcid": ["Invalid ORCID format"]}
        mock_service_instance.update_profile.return_value = (None, mock_errors)

        response = test_client.post(
            "/profile/edit", data={"name": "N", "surname": "A", "orcid": "1234"}, follow_redirects=False
        )

    assert response.status_code == 200
    assert response.status_code == 200

    logout(test_client)


# --- Tests para 2FA (Enable, Verify, Disable) ---


def test_enable_2fa_page_get_success(test_client):
    user_email = "user@example.com"
    login(test_client, user_email, "test1234")

    response = test_client.get("/profile/enable-2fa")

    assert response.status_code == 200
    assert b"Configure Two-Factor Authentication" in response.data

    logout(test_client)


def test_enable_2fa_fail_no_profile_redirect(test_client, monkeypatch):
    login(test_client, "user@example.com", "test1234")

    # Mockear current_user.profile para simular que no hay perfil
    monkeypatch.setattr("app.modules.profile.routes.current_user", MagicMock(profile=None, is_authenticated=True))

    response = test_client.get("/profile/enable-2fa", follow_redirects=False)

    assert response.status_code == 302
    assert response.location == url_for("profile.my_profile", _external=False)

    logout(test_client)


def test_verify_2fa_post_fail_no_secret_redirect(test_client):
    user_email = "user@example.com"
    login(test_client, user_email, "test1234")

    # 1. Asegurar que el usuario no tiene secreto cifrado (AttributeError corregido)
    with test_client.application.app_context():
        user, profile = get_fresh_user_and_profile(user_email)
        profile.twofa_secret = None
        profile.save()

    # 2. Intentar POST de verificación
    response = test_client.post("/profile/verify-2fa", data=dict(token="123456"), follow_redirects=False)

    # Debe redirigir a enable_2fa
    assert response.status_code == 302
    assert response.location == url_for("profile.enable_2fa", _external=False)

    logout(test_client)


def test_verify_2fa_post_fail_invalid_token_redirect(test_client):
    user_email = "user@example.com"
    login(test_client, user_email, "test1234")

    # 1. Generar y guardar un secreto válido para el usuario (AttributeError corregido)
    with test_client.application.app_context():
        secret = pyotp.random_base32()
        user, profile = get_fresh_user_and_profile(user_email)
        profile.set_twofa_secret(secret)
        profile.save()

    # 2. Intentar verificar con token inválido
    invalid_token = "000000"
    response = test_client.post("/profile/verify-2fa", data=dict(token=invalid_token), follow_redirects=False)

    # Debe redirigir a enable_2fa
    assert response.status_code == 302
    assert response.location == url_for("profile.enable_2fa", _external=False)

    logout(test_client)


def test_verify_2fa_post_success(test_client):
    user_email = "user@example.com"
    login(test_client, user_email, "test1234")

    # 1. Setup inicial del secreto
    with test_client.application.app_context():
        secret = pyotp.random_base32()
        user, profile = get_fresh_user_and_profile(user_email)
        profile.set_twofa_secret(secret)
        profile.save()

        db.session.expire_all()
        # Usamos un token simbólico, ya que la verificación será mockeada
        symbolic_token = "999999"

    # 2. Mockear pyotp.TOTP.verify para FORZAR TRUE y entrar en la rama de ÉXITO
    with patch("pyotp.TOTP.verify", return_value=True):
        # 3. Intentar verificar con token válido
        response = test_client.post("/profile/verify-2fa", data=dict(token=symbolic_token), follow_redirects=False)

    # Debe redirigir a my_profile
    assert response.status_code == 302
    assert response.location == url_for("profile.my_profile", _external=False)

    # 4. Verificar estado en BD (Aseguramos que el código de la rama IF se ejecutó)
    with test_client.application.app_context():
        db.session.expire_all()
        user_after, profile_after = get_fresh_user_and_profile(user_email)

        # El router DEBE haber seteado estos a True
        assert profile_after.twofa_enabled is True
        assert profile_after.twofa_confirmed is True

    logout(test_client)


def test_view_public_profile_datasets(test_client):
    """
    Verifies that a user can view another user's public profile and datasets,
    but does not see 2FA controls.
    """
    db.session.rollback()
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


def test_disable_2fa(test_client, monkeypatch):
    db.session.rollback()
    user = User(email="disable@example.com", password="pass")
    db.session.add(user)
    db.session.commit()

    profile = UserProfile(user_id=user.id, name="A", surname="B")
    profile.set_twofa_secret("ABCDEF")
    profile.twofa_enabled = True
    profile.twofa_confirmed = True
    db.session.add(profile)
    db.session.commit()

    monkeypatch.setattr("flask_login.utils._get_user", lambda: user)

    resp = test_client.get("/profile/disable-2fa", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile/summary")

    assert profile.twofa_enabled is False
    assert profile.twofa_confirmed is False
    assert profile.twofa_secret is None


def test_my_profile_summary(test_client, monkeypatch):
    db.session.rollback()
    user = User(email="summary@example.com", password="pass")
    db.session.add(user)
    db.session.commit()

    profile = UserProfile(user_id=user.id, name="A", surname="B")
    db.session.add(profile)
    db.session.commit()

    monkeypatch.setattr("flask_login.utils._get_user", lambda: user)

    resp = test_client.get("/profile/summary")
    assert resp.status_code == 200
    assert b"datasets" in resp.data


def test_edit_profile_get(test_client, monkeypatch):
    db.session.rollback()
    user = User(email="edit@example.com", password="pass")
    db.session.add(user)
    db.session.commit()

    profile = UserProfile(user_id=user.id, name="A", surname="B")
    db.session.add(profile)
    db.session.commit()

    monkeypatch.setattr("flask_login.utils._get_user", lambda: user)

    resp = test_client.get("/profile/edit")
    assert resp.status_code == 200
    assert b"name" in resp.data or b"form" in resp.data


def test_login_without_twofa(test_client, monkeypatch):
    db.session.rollback()
    user = User(email="no2fa@example.com", password="password")
    db.session.add(user)
    db.session.commit()

    # monkeypatch.setattr("flask_login.utils._get_user", lambda: None)
    monkeypatch.setattr("app.modules.auth.repositories.UserRepository.get_by_email", lambda self, email: user)

    resp = test_client.post("/login", data={"email": user.email, "password": "password"}, follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_verify_2fa_success(test_client, monkeypatch):
    db.session.rollback()
    user = User(email="verify@example.com", password="pass")
    db.session.add(user)
    db.session.commit()

    profile = UserProfile(user_id=user.id, name="Test", surname="User")
    profile.twofa_enabled = True
    profile.twofa_confirmed = True
    profile.set_twofa_secret("ABCDEF")
    db.session.add(profile)
    db.session.commit()

    monkeypatch.setattr("app.modules.auth.repositories.UserRepository.get_by_id", lambda self, id: user)
    monkeypatch.setattr("pyotp.TOTP.verify", lambda self, token: True)

    test_client.session_transaction(lambda s: s.__setitem__("pending_2fa_user_id", user.id))

    resp = test_client.post("/verify-2fa", data={"token": "123456"}, follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_get_by_user_id(test_client):
    with test_client.application.app_context():
        user, _ = get_fresh_user_and_profile()
        repo = UserProfileRepository()

        result = repo.get_by_user_id(user.id)

        assert result is not None
        assert result.user_id == user.id


# Service update profile tests
class DummyRepo:
    def __init__(self):
        self.updated = False

    def update(self, _id, **data):
        self.updated = True
        return {"id": _id, **data}


def test_update_profile_with_valid_form(monkeypatch):
    repo = DummyRepo()

    class DummyForm:
        data = {"name": "John", "surname": "Doe"}

        def validate(self):
            return True

    service = UserProfileService()
    service.repository = repo

    result, errors = service.update_profile(1, DummyForm())

    assert errors is None
    assert repo.updated is True
    assert result["id"] == 1
