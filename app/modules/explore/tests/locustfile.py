from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing


class ExploreBehavior(TaskSet):

    @task
    def explore_get(self):
        """Carga de GET /explore (render del HTML)."""
        response = self.client.get("/explore")
        if response.status_code != 200:
            print(f"GET /explore failed: {response.status_code}")

    @task
    def explore_post_query_facil(self):
        """POST básico: buscar algo por título."""
        payload = {
            "query": "dataset",
        }
        response = self.client.post("/explore", json=payload)
        if response.status_code != 200:
            print(f"POST /explore basic query failed: {response.status_code}")

    @task
    def explore_post_query_completa(self):
        """POST con todos los filtros simulando lo que hace el frontend."""
        payload = {
            "query": "dataset",
            "description": "Description",
            "authors": "Author 1",
            "affiliation": "Affiliation 1",
            "orcid": "0000-0000",
            "csv_filename": "file1.csv",
            "csv_title": "csv Model 1",
            "publication_doi": "10.1234",
            "tags": ["tag1"],
            "sorting": "newest",
            "publication_type": "beer branches",
        }

        response = self.client.post("/explore", json=payload)
        if response.status_code != 200:
            print(f"POST /explore full filters failed: {response.status_code}")


class ExploreUser(HttpUser):
    tasks = [ExploreBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
