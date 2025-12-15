from locust import HttpUser, SequentialTaskSet, between, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import fake, get_csrf_token

USER_NORMAL_EMAIL = "user1@example.com"
USER_NORMAL_PASSWORD = "1234"


class CommentBehavior(SequentialTaskSet):
    """
    Comportamiento secuencial:
    - login (oculto)
    - crear comentario
    - listar comentarios
    - borrar comentario
    """

    def on_start(self):
        # Logout previo (OCULTO en métricas)
        self.client.request("GET", "/logout", name=None)

        # Login (OCULTO en métricas)
        response = self.client.request("GET", "/login", name=None)
        csrf_token = get_csrf_token(response)

        self.client.request(
            "POST",
            "/login",
            data={
                "email": USER_NORMAL_EMAIL,
                "password": USER_NORMAL_PASSWORD,
                "csrf_token": csrf_token,
                "submit": "Login",
            },
            name=None,
            allow_redirects=False,
        )

        self.created_comment_id = None
        self.target_dataset_id = 1

    @task(3)
    def create_comment(self):
        """Crear comentario (VISIBLE en métricas)."""

        # Obtener CSRF desde una página válida (OCULTO)
        resp = self.client.request("GET", "/dataset/upload", name=None)
        csrf = get_csrf_token(resp)

        response = self.client.post(
            f"/dataset/{self.target_dataset_id}/comments",
            data={
                "content": f"Locust test comment {fake.sentence()}",
                "parent_id": "",
                "csrf_token": csrf,
            },
            name="/dataset/{id}/comments [POST] (create)",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code in (200, 201):
            try:
                data = response.json()
                if isinstance(data, dict) and data.get("id"):
                    self.created_comment_id = data["id"]
            except Exception:
                pass
        else:
            response.failure(f"Failed to create comment: {response.status_code}")

    @task(2)
    def list_comments(self):
        """Listar comentarios (VISIBLE en métricas)."""

        response = self.client.get(
            f"/dataset/{self.target_dataset_id}/comments",
            name="/dataset/{id}/comments [GET]",
        )

        if response.status_code != 200:
            response.failure(f"Failed to list comments: {response.status_code}")
            return

        try:
            data = response.json()
            if not isinstance(data, list):
                response.failure("Expected JSON list")
        except Exception:
            response.failure("Invalid JSON")

    @task(1)
    def delete_comment(self):
        """Borrar comentario creado (VISIBLE en métricas)."""

        if not self.created_comment_id:
            return

        response = self.client.delete(
            f"/comments/{self.created_comment_id}",
            name="/comments/{id} [DELETE]",
            allow_redirects=False,
        )

        if response.status_code == 200:
            self.created_comment_id = None
            self.interrupt()  # 🔴 IMPORTANTE: fin del flujo
        elif response.status_code == 403:
            self.interrupt()
        else:
            response.failure(f"Unexpected delete status: {response.status_code}")


class CommentUser(HttpUser):
    tasks = [CommentBehavior]
    wait_time = between(2, 2)
    host = get_host_for_locust_testing()
