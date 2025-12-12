import re
import time

import pyotp
from locust import HttpUser, SequentialTaskSet, TaskSet, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import fake, get_csrf_token

# Datos de usuarios para pruebas de login
USER_NORMAL_EMAIL = "user1@example.com"
USER_NORMAL_PASSWORD = "1234"
USER_2FA_EMAIL = "user2@example.com"
USER_2FA_PASSWORD = "1234"


class SignupBehavior(TaskSet):
    """Pruebas de comportamiento para el registro de usuarios."""

    @task(1)
    def signup_get(self):
        """Acceder al formulario de registro (GET)."""
        self.client.get("/signup")

    @task(2)
    def signup_successful(self):
        """Registro exitoso de un nuevo usuario."""
        response = self.client.get("/signup", name="/signup [GET]")
        csrf_token = get_csrf_token(response)

        # Usar email y datos únicos para evitar conflictos con registros anteriores
        unique_email = fake.email()
        self.client.post(
            "/signup",
            data={
                "email": unique_email,
                "password": fake.password(),
                "name": fake.first_name(),
                "surname": fake.last_name(),
                "csrf_token": csrf_token,
                "submit": "Submit",
            },
            name="/signup [POST] (Success)",
            # Esperar una redirección a /
            allow_redirects=False,
        )

    @task(1)
    def signup_email_in_use(self):
        """Registro fallido: email ya en uso (usamos uno de los sembrados)."""
        response = self.client.get("/signup", name="/signup [GET] (Existing Email)")
        csrf_token = get_csrf_token(response)

        response = self.client.post(
            "/signup",
            data={
                "email": USER_NORMAL_EMAIL,
                "password": fake.password(),
                "name": fake.first_name(),
                "surname": fake.last_name(),
                "csrf_token": csrf_token,
                "submit": "Submit",
            },
            name="/signup [POST] (Fail - Email In Use)",
        )
        # Debe fallar y mostrar el mensaje de error en la misma página
        if b"Email user1@example.com in use" not in response.content:
            response.failure(f"Expected 'Email in use' error not found.")


class LoginNormalBehavior(TaskSet):
    """Pruebas de comportamiento para el login normal (sin 2FA)."""

    def on_start(self):
        # Para asegurarse de estar deslogueado al inicio de la TaskSet
        self.client.get("/logout", name="/logout (on_start)")

    @task(1)
    def login_get(self):
        """Acceder al formulario de login (GET)."""
        self.client.get("/login")

    @task(3)
    def login_successful(self):
        """Login exitoso con un usuario normal (sin 2FA)."""
        response = self.client.get("/login", name="/login [GET] (Success)")
        csrf_token = get_csrf_token(response)

        # Usuario normal (user1@example.com)
        self.client.post(
            "/login",
            data={
                "email": USER_NORMAL_EMAIL,
                "password": USER_NORMAL_PASSWORD,
                "csrf_token": csrf_token,
                "submit": "Login",
            },
            name="/login [POST] (Success - No 2FA)",
            # Esperar una redirección a /
            allow_redirects=False,
        )
        # Cerrar sesión después del login para permitir repetición
        self.client.get("/logout", name="/logout (after success)")

    @task(2)
    def login_failed(self):
        """Login fallido: credenciales inválidas."""
        response = self.client.get("/login", name="/login [GET] (Fail)")
        csrf_token = get_csrf_token(response)

        response = self.client.post(
            "/login",
            data={
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
                "csrf_token": csrf_token,
                "submit": "Login",
            },
            name="/login [POST] (Fail - Invalid Credentials)",
        )
        # Debe fallar y mostrar el mensaje de error en la misma página
        if b"Invalid credentials" not in response.content:
            response.failure(f"Expected 'Invalid credentials' error not found.")


class Login2FABehavior(SequentialTaskSet):
    """Pruebas de comportamiento para el login con 2FA (proceso de 2 pasos)."""

    def on_start(self):
        # 1. Asegurarse de estar deslogueado
        self.client.get("/logout", name="/logout (on_start)")
        self.twofa_secret = None

    @task
    def login_step_1_2fa_redirect(self):
        """Paso 1: Intentar login con usuario 2FA, esperar redirección a /verify-2fa."""
        response = self.client.get("/login", name="/login [GET] (2FA)")
        csrf_token = get_csrf_token(response)

        response = self.client.post(
            "/login",
            data={"email": USER_2FA_EMAIL, "password": USER_2FA_PASSWORD, "csrf_token": csrf_token, "submit": "Login"},
            name="/login [POST] (Redirect to 2FA)",
            allow_redirects=False,
        )

        # Comprobamos que el usuario está configurado para 2FA y la redirección es correcta
        if response.status_code == 302 and "/verify-2fa" in response.headers.get("Location", ""):
            pass
        else:
            response.failure("Did not redirect to /verify-2fa as expected.")
            self.interrupt()

        self.twofa_secret = "JBSWY3DPEHPK3PXP"

        if not self.twofa_secret:
            print("WARNING: twofa_secret is missing. 2FA verification cannot be tested.")
            self.interrupt()  # Detener si no hay secreto

    @task
    def login_step_2_2fa_success(self):
        """Paso 2: Verificar el código 2FA correctamente."""
        # Generar un token TOTP válido con el secreto simulado
        totp = pyotp.TOTP(self.twofa_secret)
        valid_token = totp.now()

        # Acceder a la página de verificación (GET)
        self.client.get("/verify-2fa", name="/verify-2fa [GET]")

        # Enviar el token correcto (POST)
        response = self.client.post(
            "/verify-2fa", data={"token": valid_token}, name="/verify-2fa [POST] (Success)", allow_redirects=False
        )

        if response.status_code == 302 and response.headers.get("Location") == "/":
            pass
        else:
            response.failure("2FA verification failed or did not redirect to /.")

        # Cerrar sesión para que la TaskSet pueda repetirse
        self.client.get("/logout", name="/logout (after 2FA success)")

    @task
    def login_step_2_2fa_failure(self):
        """Paso 2: Verificar el código 2FA incorrectamente."""
        if not self.twofa_secret:
            self.interrupt()

        # Enviar un token incorrecto (p. ej., '000000')
        incorrect_token = "000000"

        # Acceder a la página de verificación (GET)
        self.client.get("/verify-2fa", name="/verify-2fa [GET] (Fail)")

        # Enviar el token incorrecto (POST)
        response = self.client.post(
            "/verify-2fa", data={"token": incorrect_token}, name="/verify-2fa [POST] (Fail - Invalid Code)"
        )

        # Debe mostrar el error en la misma página (no hay redirección de éxito)
        if b"Invalid code. Try again." not in response.content:
            response.failure(f"Expected 'Invalid code' error not found.")

        self.client.get("/logout", name="/logout (after 2FA failure to reset session)")


class LogoutBehavior(TaskSet):
    """Pruebas de comportamiento para el logout."""

    def on_start(self):
        """Asegurarse de estar logueado antes de intentar el logout."""
        # Login del usuario normal (sin 2FA)
        response = self.client.get("/login", name="/login [GET] (pre-logout)")
        csrf_token = get_csrf_token(response)
        self.client.post(
            "/login",
            data={"email": USER_NORMAL_EMAIL, "password": USER_NORMAL_PASSWORD, "csrf_token": csrf_token},
            name="/login [POST] (pre-logout)",
            allow_redirects=False,
        )

    @task
    def logout_successful(self):
        """Logout exitoso."""
        response = self.client.get("/logout", name="/logout [GET] (Success)", allow_redirects=False)

        # Esperar redirección a /
        if response.status_code == 302 and response.headers.get("Location") == "/":
            pass  # Éxito
        else:
            response.failure("Logout failed or did not redirect to /.")


class AuthUser(HttpUser):
    """Clase principal de Locust que define la carga de trabajo."""

    tasks = {
        SignupBehavior: 2,
        LoginNormalBehavior: 3,
        Login2FABehavior: 1,
        LogoutBehavior: 1,
    }
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
