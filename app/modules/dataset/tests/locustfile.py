import os

from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import get_csrf_token


class DatasetBehavior(TaskSet):

    def on_start(self):
        # Simple navegación inicial
        self.dataset_page()

    # --------------------------------------------------
    # 1) Cargar la página de upload
    # --------------------------------------------------
    @task
    def dataset_page(self):
        response = self.client.get("/dataset/upload")
        self.csrf = get_csrf_token(response)

    # --------------------------------------------------
    # 2) Validar CSV 
    # --------------------------------------------------
    @task
    def validate_csv(self):
        valid_csv = "col1,col2,col3\n1,2,3\n4,5,6"

        payload = {
            "content": valid_csv,
        }

        response = self.client.post(
            "/dataset/file/validate",
            json=payload,
        )
        self.csrf = get_csrf_token(response)

    @task
    def upload_valid_csv(self):
        """Sube un CSV válido y espera 200."""
        file_path = os.path.abspath("app/modules/dataset/csv_examples/file1.csv")

        with open(file_path, "rb") as f:
            files = {"file": ("file1.csv", f, "text/csv")}
            self.client.post("/dataset/file/upload", files=files)

    @task
    def upload_invalid_csv(self):
        """Sube un CSV inválido (malas cabeceras o columnas incorrectas)."""
        file_path = os.path.abspath("app/modules/dataset/csv_examples/file15.csv")

        with open(file_path, "rb") as f:
            files = {"file": ("file15.csv", f, "text/csv")}
            self.client.post("/dataset/file/upload", files=files)


class DatasetUser(HttpUser):
    tasks = [DatasetBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
