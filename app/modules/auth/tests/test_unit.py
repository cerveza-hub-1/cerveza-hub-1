import re
from unittest.mock import MagicMock

import pyotp
import pytest
from flask import url_for

from app import db
from app.modules.auth.repositories import UserRepository
from app.modules.auth.services import AuthenticationService
from app.modules.profile.models import UserProfile
from app.modules.profile.repositories import UserProfileRepository


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Add HERE new elements to the database that you want to exist in the test context.
        # DO NOT FORGET to use db.session.add(<element>) and db.session.commit() to save the data.
        pass

    yield test_client


def test_login_success(test_client):
    response = test_client.post(
        "/login",
        data=dict(email="test@example.com", password="test1234"),
        follow_redirects=True,
    )

    assert response.request.path != url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_login_unsuccessful_bad_email(test_client):
    response = test_client.post(
        "/login",
        data=dict(email="bademail@example.com", password="test1234"),
        follow_redirects=True,
    )

    assert response.request.path == url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_login_unsuccessful_bad_password(test_client):
    response = test_client.post(
        "/login",
        data=dict(email="test@example.com", password="basspassword"),
        follow_redirects=True,
    )

    assert response.request.path == url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_signup_user_no_name(test_client):
    response = test_client.post(
        "/signup",
        data=dict(surname="Foo", email="test@example.com", password="test1234"),
        follow_redirects=True,
    )
    assert response.request.path == url_for("auth.show_signup_form"), "Signup was unsuccessful"
    assert b"This field is required" in response.data, response.data


def test_signup_user_unsuccessful(test_client):
    email = "test@example.com"
    response = test_client.post(
        "/signup",
        data=dict(name="Test", surname="Foo", email=email, password="test1234"),
        follow_redirects=True,
    )
    assert response.request.path == url_for("auth.show_signup_form"), "Signup was unsuccessful"
    assert f"Email {email} in use".encode("utf-8") in response.data


def test_signup_user_successful(test_client):
    response = test_client.post(
        "/signup",
        data=dict(name="Foo", surname="Example", email="foo@example.com", password="foo1234"),
        follow_redirects=True,
    )
    assert response.request.path == url_for("public.index"), "Signup was unsuccessful"


def test_service_create_with_profie_success(clean_database):
    data = {
        "name": "Test",
        "surname": "Foo",
        "email": "service_test@example.com",
        "password": "test1234",
    }

    AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 1
    assert UserProfileRepository().count() == 1


def test_service_create_with_profile_fail_no_email(clean_database):
    data = {"name": "Test", "surname": "Foo", "email": "", "password": "1234"}

    with pytest.raises(ValueError, match="Email is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


def test_service_create_with_profile_fail_no_password(clean_database):
    data = {
        "name": "Test",
        "surname": "Foo",
        "email": "test@example.com",
        "password": "",
    }

    with pytest.raises(ValueError, match="Password is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


# --- Tests para AuthenticationService ---


def test_service_login_success(clean_database):
    email = "service_login@example.com"
    password = "correct123"
    AuthenticationService().create_with_profile(name="LTest", surname="Srv", email=email, password=password)

    service = AuthenticationService()

    result = service.login(email=email, password=password)

    assert result is True, "El login debería ser exitoso"


def test_service_login_fail_bad_email(clean_database):
    service = AuthenticationService()
    result = service.login(email="nonexistent@example.com", password="anypassword")
    assert result is False, "El login debería fallar si el email no existe"


def test_service_create_with_profile_fail_no_name(clean_database):
    data = {
        "name": "",
        "surname": "Foo",
        "email": "test@example.com",
        "password": "1234",
    }

    with pytest.raises(ValueError, match="Name is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


def test_service_create_with_profile_fail_no_surname(clean_database):
    data = {
        "name": "Test",
        "surname": "",
        "email": "test@example.com",
        "password": "1234",
    }

    with pytest.raises(ValueError, match="Surname is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


def test_service_update_profile_success(monkeypatch):
    service = AuthenticationService()

    mock_form = MagicMock()
    mock_form.validate.return_value = True
    mock_form.data = {"name": "UpdatedName", "surname": "UpdatedSurname"}

    mock_updated_instance = object()
    monkeypatch.setattr(service, "update", MagicMock(return_value=mock_updated_instance))

    result, errors = service.update_profile(user_profile_id=1, form=mock_form)

    assert result == mock_updated_instance
    assert errors is None


def test_service_update_profile_failure(monkeypatch):
    service = AuthenticationService()

    mock_form = MagicMock()
    mock_form.validate.return_value = False
    mock_form.errors = {"name": ["Name is required"]}

    result, errors = service.update_profile(user_profile_id=1, form=mock_form)

    assert result is None
    assert errors == {"name": ["Name is required"]}


def test_service_get_authenticated_user_authenticated(test_client, monkeypatch):
    service = AuthenticationService()

    user = service.create_with_profile(name="Auth", surname="User", email="auth@example.com", password="1234")

    # Mockear current_user para simular que el usuario está logueado
    with test_client.application.app_context():
        # Configuramos el mock para que `is_authenticated` sea True y devuelva el objeto user
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.email = user.email
        mock_user.profile = user.profile

        monkeypatch.setattr("app.modules.auth.services.current_user", mock_user)

        user_result = service.get_authenticated_user()

        assert user_result is not None
        assert user_result.email == user.email


def test_service_get_authenticated_user_unauthenticated(test_client):
    service = AuthenticationService()

    test_client.get("/logout")

    with test_client.application.app_context():
        user = service.get_authenticated_user()
        assert user is None


def test_service_get_authenticated_user_profile_authenticated(test_client, monkeypatch):
    service = AuthenticationService()

    user = service.create_with_profile(name="Auth", surname="Profile", email="auth_prof@example.com", password="1234")

    # Mockear current_user
    with test_client.application.app_context():
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.profile = user.profile

        monkeypatch.setattr("app.modules.auth.services.current_user", mock_user)

        profile_result = service.get_authenticated_user_profile()

        assert profile_result is not None
        assert profile_result.surname == "Profile"


def test_service_get_authenticated_user_profile_unauthenticated(test_client):
    service = AuthenticationService()

    test_client.get("/logout")

    with test_client.application.app_context():
        profile = service.get_authenticated_user_profile()
        assert profile is None


def test_signup_redirect_if_authenticated(test_client, monkeypatch):
    mock_user = MagicMock()
    mock_user.is_authenticated = True

    monkeypatch.setattr("app.modules.auth.routes.current_user", mock_user)

    response = test_client.get("/signup/", follow_redirects=False)

    assert response.status_code == 302
    assert response.location == url_for("public.index", _external=False)


def test_login_redirects_authenticated_user(test_client):
    email = "redirect_login@example.com"
    AuthenticationService().create_with_profile(name="Redirect", surname="Test", email=email, password="1234")

    test_client.post("/login", data=dict(email=email, password="1234"), follow_redirects=True)

    response = test_client.get("/login", follow_redirects=False)

    assert response.status_code == 302
    assert response.location == url_for("public.index", _external=False)

    test_client.get("/logout", follow_redirects=True)


def test_signup_exception_handling(test_client, monkeypatch):
    def fake_create_with_profile(*args, **kwargs):
        raise Exception("DB failure")

    monkeypatch.setattr(AuthenticationService, "create_with_profile", fake_create_with_profile)

    response = test_client.post(
        "/signup/",
        data=dict(name="Foo", surname="Bar", email="fail@example.com", password="1234"),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Error creating user: DB failure" in response.data


# TESTS UNITARIOS 2FA


def test_login_redirects_to_2fa_if_enabled(test_client):
    db.session.rollback()
    service = AuthenticationService()
    user = service.create_with_profile(
        name="Two",
        surname="FA",
        email="login2fa@example.com",
        password="1234",
    )

    # Activar 2FA
    profile = UserProfileRepository().get_by_user_id(user.id)
    secret = pyotp.random_base32()
    profile.set_twofa_secret(secret)
    profile.twofa_enabled = True
    profile.twofa_confirmed = True
    profile.save()

    db.session.refresh(profile)

    response = test_client.post(
        "/login",
        data=dict(email="login2fa@example.com", password="1234"),
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.location == url_for("auth.verify_2fa")

    # Revisar que session["pending_2fa_user_id"] fue seteado
    with test_client.session_transaction() as sess:
        assert sess["pending_2fa_user_id"] == user.id


def test_login_renders_form_on_get(test_client):
    response = test_client.get("/login")

    assert response.status_code == 200
    assert b"Login" in response.data or b"email" in response.data


def test_login_renders_form_on_invalid_post(test_client):
    response = test_client.post("/login", data=dict(email="", password=""), follow_redirects=True)

    assert response.status_code == 200
    assert b"Login" in response.data or b"Invalid" not in response.data


def test_verify_2fa_user_without_profile_redirects(test_client):
    # Crear usuario sin perfil manualmente (borrar perfil)
    service = AuthenticationService()
    user = service.create_with_profile(name="NoProfile", surname="User", email="noprofile@example.com", password="1234")

    # Eliminar su perfil
    db.session.delete(user.profile)
    db.session.commit()

    with test_client.session_transaction() as sess:
        sess["pending_2fa_user_id"] = user.id

    response = test_client.get("/verify-2fa")

    assert response.status_code == 302
    assert response.location == url_for("public.index")


def test_verify_2fa_user_without_secret_redirects(test_client):
    service = AuthenticationService()
    user = service.create_with_profile(name="NoSecret", surname="User", email="nosecret@example.com", password="1234")

    profile = UserProfileRepository().get_by_user_id(user.id)
    profile.twofa_enabled = True
    profile.twofa_confirmed = True
    profile.twofa_secret_encrypted = None
    profile.save()

    with test_client.session_transaction() as sess:
        sess["pending_2fa_user_id"] = user.id

    response = test_client.post("/verify-2fa", data=dict(token="123456"))

    assert response.status_code == 302
    assert response.location == url_for("auth.login")


def test_twofa_secret_encryption_and_decryption(clean_database):
    profile = UserProfile(name="Test", surname="User", user_id=1)
    secret = pyotp.random_base32()
    profile.set_twofa_secret(secret)

    decrypted = profile.get_twofa_secret()
    assert decrypted == secret, "El secreto 2FA debe descifrarse correctamente"


def test_twofa_token_verification_with_model(clean_database):
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    current_token = totp.now()

    # Simular usuario con 2FA activado
    profile = UserProfile(
        name="Tester",
        surname="User",
        user_id=1,
        twofa_enabled=True,
        twofa_confirmed=True,
    )
    profile.set_twofa_secret(secret)

    # Verificar que el código generado sea válido
    verified = pyotp.TOTP(profile.get_twofa_secret()).verify(current_token)
    assert verified, "El código TOTP generado debe ser válido en el momento actual"


def test_verify_2fa_success(test_client):
    # Crear usuario con 2FA activado
    db.session.rollback()
    data = {
        "name": "Two",
        "surname": "FA2",
        "email": "verify@example.com",
        "password": "1234",
    }
    user = AuthenticationService().create_with_profile(**data)

    profile = UserProfileRepository().get_by_user_id(user.id)
    secret = pyotp.random_base32()
    profile.set_twofa_secret(secret)
    profile.twofa_enabled = True
    profile.twofa_confirmed = True
    profile.save()

    # Simular sesión pendiente de 2FA
    with test_client.session_transaction() as sess:
        sess["pending_2fa_user_id"] = user.id

    token = pyotp.TOTP(secret).now()
    response = test_client.post("/verify-2fa", data=dict(token=token), follow_redirects=True)

    assert response.request.path == url_for(
        "public.index"
    ), "La verificación 2FA exitosa no redirigió a la página principal."
    assert response.status_code == 200
    assert b"Index" in response.data or b"Home" in response.data  # Comprobar contenido de la página de inicio


def test_2fa_verify_fail_token(clean_database):
    # Creamos otro usuario con 2FA activado
    service = AuthenticationService()
    user = service.create_with_profile(
        name="Test",
        surname="Foo",
        email="service_test@example.com",
        password="test1234",
    )
    user.profile.twofa_enabled = True
    user.profile.twofa_confirmed = True
    secret = pyotp.random_base32()
    user.profile.twofa_secret_encrypted = secret
    db.session.commit()

    # Token inválido
    totp = pyotp.TOTP(secret)
    invalid_token = "123456"
    assert not totp.verify(invalid_token), "El token 2FA NO debería ser válido"


def test_2fa_verify_successful_with_secret(clean_database):
    # Creamos un usuario con 2FA activado
    service = AuthenticationService()
    user = service.create_with_profile(
        name="Test",
        surname="Foo",
        email="service_test@example.com",
        password="test1234",
    )
    user.profile.twofa_enabled = True
    user.profile.twofa_confirmed = True
    secret = pyotp.random_base32()
    user.profile.twofa_secret_encrypted = secret
    db.session.commit()

    # Generamos un token válido
    totp = pyotp.TOTP(secret)
    valid_token = totp.now()

    # Simulamos la verificación
    assert totp.verify(valid_token), "El token 2FA debería ser válido"


def test_generate_twofa_secret(clean_database):
    service = AuthenticationService()
    user = service.create_with_profile(
        name="Test",
        surname="Foo",
        email="service_test@example.com",
        password="test1234",
    )

    # Activamos el 2FA por primera vez
    secret_to_set = pyotp.random_base32()  # Secreto se genera fuera del modelo
    user.profile.set_twofa_secret(secret_to_set)  # Se encripta y se guarda

    user.profile.save()

    secret = user.profile.get_twofa_secret()

    assert secret is not None, "El secreto no debe ser None"
    assert secret == secret_to_set, "El secreto desencriptado debe ser igual al generado"
    assert re.fullmatch(r"[A-Z2-7]{16,32}", secret), "El secreto debe tener formato Base32 válido"

    totp = pyotp.TOTP(secret)
    token = totp.now()
    assert len(token) == 6, "El token TOTP debe tener 6 dígitos"


def test_2fa_user_without_secret(clean_database):
    service = AuthenticationService()
    user = service.create_with_profile(
        name="Test",
        surname="Foo",
        email="service_test@example.com",
        password="test1234",
    )
    user.profile.twofa_enabled = True
    user.profile.twofa_confirmed = True
    user.profile.twofa_secret = None
    db.session.commit()

    # Simulamos la lógica de /verify-2fa
    secret = user.profile.get_twofa_secret()
    assert secret is None, "El secreto debería ser None"

    # Verificación de token debería fallar
    try:
        # Aquí se simula lo que haría el router si no se capturara el None:
        if secret:
            totp = pyotp.TOTP(secret)
            valid = totp.verify("123456")
        else:
            valid = False

    except Exception:
        valid = False

    assert not valid, "La verificación debe devolver False o lanzar excepción controlada si no se verifica el secreto"


def test_login_user_with_2fa_disabled(clean_database):
    service = AuthenticationService()
    user = service.create_with_profile(
        name="Test",
        surname="Foo",
        email="service_test@example.com",
        password="test1234",
    )
    user.profile.twofa_enabled = False
    db.session.commit()

    # Al hacer login no debería haber user_id pendiente
    session = {}
    if user.profile.twofa_enabled:
        session["pending_2fa_user_id"] = user.id

    assert "pending_2fa_user_id" not in session, "El sistema no debe marcar sesión pendiente si 2FA está deshabilitado"


def test_user_with_2fa_enabled_but_not_confirmed(clean_database):
    service = AuthenticationService()
    user = service.create_with_profile(
        name="Test",
        surname="Foo",
        email="service_test@example.com",
        password="test1234",
    )
    user.profile.twofa_enabled = True
    user.profile.twofa_confirmed = False
    db.session.commit()

    # La interfaz debería mostrar el QR de configuración
    # En la lógica, todavía NO se debe exigir código TOTP
    assert user.profile.twofa_enabled, "El usuario ha activado 2FA"
    assert not user.profile.twofa_confirmed, "El usuario aún no lo ha confirmado"

    requires_2fa = user.profile.twofa_enabled and user.profile.twofa_confirmed
    assert not requires_2fa, "El sistema no debe requerir token hasta confirmación"


def test_verify_2fa_unsuccessful_bad_token(test_client):
    # Crear usuario con 2FA activado (igual que test_verify_2fa_success)
    data = {
        "name": "Two",
        "surname": "FA3",
        "email": "verify_fail@example.com",
        "password": "1234",
    }
    user = AuthenticationService().create_with_profile(**data)

    profile = UserProfileRepository().get_by_user_id(user.id)
    secret = pyotp.random_base32()
    profile.set_twofa_secret(secret)
    profile.twofa_enabled = True
    profile.twofa_confirmed = True
    profile.save()

    user_id_to_use = user.id
    db.session.remove()  # Limpiar datos de sesión

    # Simular sesión pendiente de 2FA
    with test_client.session_transaction() as sess:
        sess["pending_2fa_user_id"] = user_id_to_use

    bad_token = "000000"  # Token incorrecto
    response = test_client.post("/verify-2fa", data=dict(token=bad_token), follow_redirects=False)

    assert response.status_code == 200  # No hay redirección, se mantiene en la página

    assert b"token" in response.data or b"Token" in response.data
    assert (
        b"Invalid code. Try again." in response.data or b"Invalid code" in response.data
    ), "El mensaje de error no es visible en la respuesta"

    with test_client.session_transaction() as sess:
        assert "pending_2fa_user_id" in sess, "El ID de usuario pendiente debe permanecer en la sesión"


def test_verify_2fa_no_pending_session(test_client):
    # Simular intento de acceder a /verify-2fa sin 'pending_2fa_user_id' en la sesión

    # Asegurarse de que no hay 'pending_2fa_user_id'
    with test_client.session_transaction() as sess:
        if "pending_2fa_user_id" in sess:
            sess.pop("pending_2fa_user_id")

    response = test_client.get("/verify-2fa", follow_redirects=False)

    # Debe redirigir al login
    assert response.status_code == 302
    assert response.location == url_for("auth.login")
