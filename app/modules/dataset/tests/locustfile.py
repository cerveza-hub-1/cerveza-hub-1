import os

from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import get_csrf_token


class DatasetBehavior(TaskSet):

    def on_start(self):
        # Login
        login_page = self.client.get("/login")
        csrf_token = get_csrf_token(login_page)

        login_data = {
            "username": "user1@example.com",  # corrige el typo en "exameple"
            "password": "1234",
            "csrf_token": csrf_token,
        }
        response = self.client.post("/login", data=login_data)
        if response.status_code != 200:
            print(f"Login fallido: {response.status_code} - {response.text}")
        else:
            print("Login exitoso")

        # IDs fijos para probar datasets con DOI y no sincronizados
        self.dataset_with_doi = "10.1234/dataset1/"  # Ajusta al ID real con DOI en tu base

        # Navegación inicial
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

    # --------------------------------------------------
    # 3) Visualización de dataset con DOI
    # --------------------------------------------------
    @task
    def view_dataset_with_doi(self):
        """Accede a la vista de un dataset con DOI."""
        if self.dataset_with_doi:
            with self.client.get(f"/doi/{self.dataset_with_doi}", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Status {response.status_code}: {response.text}")


class DatasetUser(HttpUser):
    tasks = [DatasetBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
