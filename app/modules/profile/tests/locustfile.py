import re

import pyotp
from locust import HttpUser, SequentialTaskSet, TaskSet, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import fake, get_csrf_token

# Datos de usuarios pre-sembrados
USER_NORMAL_EMAIL = "user1@example.com"
USER_NORMAL_PASSWORD = "1234"
USER_OTHER_ID = 2  # user2@example.com tiene el ID 2


def login_user(client, email, password, name="Login (pre-task)"):
    """Función auxiliar para loguear un usuario y obtener el CSRF token."""
    client.get("/logout", name=f"/logout ({name})")
    response = client.get("/login", name=f"/login [GET] ({name})")
    csrf_token = get_csrf_token(response)

    client.post(
        "/login",
        data={
            "email": email,
            "password": password,
            "csrf_token": csrf_token,
            "submit": "Login",
        },
        name=f"/login [POST] ({name})",
        allow_redirects=False,
    )


class ViewProfileBehavior(TaskSet):
    """Pruebas de comportamiento para la visualización del perfil."""

    def on_start(self):
        login_user(self.client, USER_NORMAL_EMAIL, USER_NORMAL_PASSWORD, "ViewProfile")

    @task(3)
    def view_my_profile_summary(self):
        """Acceder a la página de resumen de perfil propio."""
        self.client.get("/profile/summary", name="/profile/summary (My Profile)")

    @task(1)
    def view_public_profile(self):
        """Acceder al perfil público de otro usuario (user2)."""
        # Se asume que el user2 existe y tiene ID 2 basado en auth/seeders.py
        self.client.get(
            f"/profile/{USER_OTHER_ID}",
            name="/profile/{user_id} (Public Profile)"
        )


class EditProfileBehavior(TaskSet):
    """Pruebas de comportamiento para la edición del perfil."""

    def on_start(self):
        login_user(self.client, USER_NORMAL_EMAIL, USER_NORMAL_PASSWORD, "EditProfile")

    @task(1)
    def get_edit_profile(self):
        """Acceder al formulario de edición de perfil (GET)."""
        self.client.get("/profile/edit", name="/profile/edit [GET]")

    @task(3)
    def post_edit_profile_success(self):
        """Edición de perfil exitosa con nuevos datos válidos."""
        response = self.client.get(
            "/profile/edit", name="/profile/edit [GET] (Post Success)"
        )
        csrf_token = get_csrf_token(response)

        new_name = fake.first_name()
        new_surname = fake.last_name()
        new_affiliation = fake.company()

        orcid_format = "{}-{}-{}-{}".format(
            fake.random_number(digits=4),
            fake.random_number(digits=4),
            fake.random_number(digits=4),
            fake.random_number(digits=4),
        )

        self.client.post(
            "/profile/edit",
            data={
                "name": new_name,
                "surname": new_surname,
                "orcid": orcid_format,
                "affiliation": new_affiliation,
                "csrf_token": csrf_token,
                "submit": "Save profile",
            },
            name="/profile/edit [POST] (Success)",
        )

    @task(1)
    def post_edit_profile_invalid_orcid(self):
        """Edición de perfil fallida debido a un formato ORCID inválido."""
        response = self.client.get("/profile/edit", name="/profile/edit [GET] (Post Fail)")
        csrf_token = get_csrf_token(response)

        invalid_orcid = "1234567890123456789"  # Longitud incorrecta o formato

        response = self.client.post(
            "/profile/edit",
            data={
                "name": fake.first_name(),
                "surname": fake.last_name(),
                "orcid": invalid_orcid,
                "affiliation": fake.company(),
                "csrf_token": csrf_token,
                "submit": "Save profile",
            },
            name="/profile/edit [POST] (Fail - Invalid ORCID)",
        )

        if response.status_code != 200:
            response.failure(
                f"Expected 200 status code on form validation failure, got {response.status_code}"
            )


class TwoFABehavior(SequentialTaskSet):
    """
    Pruebas secuenciales para habilitar, verificar y deshabilitar 2FA.
    """

    def on_start(self):
        login_user(self.client, USER_NORMAL_EMAIL, USER_NORMAL_PASSWORD, "2FA Setup")
        self.twofa_secret = None

    @task
    def step_1_enable_2fa(self):
        """Ruta: /profile/enable-2fa (GET) - Inicia la configuración y obtiene el secreto."""
        response = self.client.get("/profile/enable-2fa", name="/profile/enable-2fa [GET]")

        # Capturamos el secreto, ya sea entre comillas o después de 'secret:'
        secret_match = re.search(r'secret="([A-Z2-7=]{16,})"|secret: (\w+)', response.text)

        if secret_match:
            self.twofa_secret = secret_match.group(1) or secret_match.group(2)
            self.client.environment.catch_response(response)  # Marcar como exitosa si se encuentra el secreto
        else:
            response.failure("2FA secret not found in response. Cannot continue 2FA flow.")
            self.interrupt()  # Detener la secuencia si no se obtiene el secreto

    @task
    def step_2_verify_2fa_success(self):
        """Ruta: /profile/verify-2fa (POST) - Verifica el 2FA con un código correcto."""
        if not self.twofa_secret:
            return

        # Generar código TOTP con el secreto obtenido
        totp = pyotp.TOTP(self.twofa_secret)
        valid_token = totp.now()

        response = self.client.post(
            "/profile/verify-2fa",
            data={"token": valid_token},
            name="/profile/verify-2fa [POST] (Success)",
            allow_redirects=False,
        )

        if response.status_code == 302 and "/profile/summary" in response.headers.get("Location", ""):
            pass
        else:
            response.failure("2FA verification failed or did not redirect to /profile/summary.")
            self.interrupt()

    @task
    def step_3_verify_2fa_failure(self):
        """Ruta: /profile/verify-2fa (POST) - Verifica el 2FA con un código incorrecto."""
        # Se simula una verificación fallida antes de deshabilitar
        if not self.twofa_secret:
            return

        incorrect_token = "000000"

        # Simular una verificación fallida (esperamos redirección a enable-2fa)
        response = self.client.post(
            "/profile/verify-2fa",
            data={"token": incorrect_token},
            name="/profile/verify-2fa [POST] (Fail)",
            allow_redirects=False,
        )

        if response.status_code == 302 and "/profile/enable-2fa" in response.headers.get("Location", ""):
            pass
        else:
            response.failure("Expected redirection to enable-2fa on failed verification.")
            self.interrupt()

    @task
    def step_4_disable_2fa(self):
        """Ruta: /profile/disable-2fa - Deshabilita el 2FA."""
        response = self.client.get("/profile/disable-2fa", name="/profile/disable-2fa")

        # Esperar redirección a /profile/summary
        if response.status_code == 302 and "/profile/summary" in response.headers.get("Location", ""):
            pass
        else:
            response.failure("2FA disable failed or did not redirect to /profile/summary.")

        # Logout al final de la secuencia completa
        self.client.get("/logout", name="/logout (after 2FA flow)")


class ProfileUser(HttpUser):
    """Clase principal de Locust para las pruebas de perfil."""

    tasks = {
        ViewProfileBehavior: 5,
        EditProfileBehavior: 3,
        TwoFABehavior: 1,  # Baja prioridad ya que modifica la BD
    }
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
