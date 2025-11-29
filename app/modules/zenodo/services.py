import logging
import os
import uuid

import requests
from dotenv import load_dotenv
from flask import Response, jsonify
from flask_login import current_user

from app.modules.dataset.models import DataSet
from app.modules.featuremodel.models import FeatureModel
from app.modules.zenodo.repositories import ZenodoRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)

load_dotenv()


class ZenodoService(BaseService):

    def get_zenodo_url(self):
        fakenodo_url = os.getenv("FAKENODO_URL")
        if fakenodo_url:
            return fakenodo_url

        FLASK_ENV = os.getenv("FLASK_ENV", "development")
        ZENODO_API_URL = ""

        if FLASK_ENV == "development":
            ZENODO_API_URL = os.getenv("ZENODO_API_URL", "https://sandbox.zenodo.org/api/deposit/depositions")
        elif FLASK_ENV == "production":
            ZENODO_API_URL = os.getenv("ZENODO_API_URL", "https://zenodo.org/api/deposit/depositions")
        else:
            ZENODO_API_URL = os.getenv("ZENODO_API_URL", "https://sandbox.zenodo.org/api/deposit/depositions")

        return ZENODO_API_URL

    def get_zenodo_access_token(self):
        return os.getenv("ZENODO_ACCESS_TOKEN")

    def __init__(self):
        super().__init__(ZenodoRepository())
        self.ZENODO_API_URL = self.get_zenodo_url()
        self.is_fakenodo = bool(os.getenv("FAKENODO_URL"))
        self.headers = {"Content-Type": "application/json"}
        self.params = {} if self.is_fakenodo else {"access_token": self.get_zenodo_access_token()}

    def test_connection(self) -> bool:
        """
        Test the connection with Zenodo.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        response = requests.get(self.ZENODO_API_URL, params=self.params, headers=self.headers)
        return response.status_code == 200

    def test_full_connection(self) -> Response:
        """
        Test the connection with Zenodo by creating a deposition, uploading an empty test file, and deleting the
        deposition.

        Returns:
            bool: True if the connection, upload, and deletion are successful, False otherwise.
        """

        success = True

        # Create a test file
        working_dir = os.getenv("WORKING_DIR", "")
        file_path = os.path.join(working_dir, "test_file.txt")
        with open(file_path, "w") as f:
            f.write("This is a test file with some content.")

        messages = []  # List to store messages

        # Step 1: Create a deposition on Zenodo
        data = {
            "metadata": {
                "title": "Test Deposition",
                "upload_type": "dataset",
                "description": "This is a test deposition created via Zenodo API",
                "creators": [{"name": "John Doe"}],
            }
        }

        response = requests.post(self.ZENODO_API_URL, json=data, params=self.params, headers=self.headers)

        if response.status_code != 201:
            return jsonify(
                {
                    "success": False,
                    "messages": f"Failed to create test deposition on Zenodo. Response code: {response.status_code}",
                }
            )

        deposition_id = response.json()["id"]

        # Step 2: Upload an empty file to the deposition
        data = {"name": "test_file.txt"}
        files = {"file": open(file_path, "rb")}
        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/files"
        response = requests.post(publish_url, params=self.params, data=data, files=files)
        files["file"].close()  # Close the file after uploading

        logger.info(f"Publish URL: {publish_url}")
        logger.info(f"Params: {self.params}")
        logger.info(f"Data: {data}")
        logger.info(f"Files: {files}")
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Content: {response.content}")

        if response.status_code != 201:
            messages.append(f"Failed to upload test file to Zenodo. Response code: {response.status_code}")
            success = False

        # Step 3: Delete the deposition
        response = requests.delete(f"{self.ZENODO_API_URL}/{deposition_id}", params=self.params)

        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({"success": success, "messages": messages})

    def get_all_depositions(self) -> dict:
        """
        Get all depositions from Zenodo.

        Returns:
            dict: The response in JSON format with the depositions.
        """
        response = requests.get(self.ZENODO_API_URL, params=self.params, headers=self.headers)
        if response.status_code != 200:
            raise Exception("Failed to get depositions")
        return response.json()

    def create_new_deposition(self, dataset: DataSet) -> dict:
        """
        Create a new deposition in Zenodo or Fakenodo.
        """
        logger.info("Dataset sending to Zenodo/Fakenodo...")
        logger.info(f"Publication type...{dataset.ds_meta_data.publication_type.value}")

        metadata = {
            "title": dataset.ds_meta_data.title,
            "upload_type": "dataset" if dataset.ds_meta_data.publication_type.value == "none" else "publication",
            "publication_type": (
                dataset.ds_meta_data.publication_type.value
                if dataset.ds_meta_data.publication_type.value != "none"
                else None
            ),
            "description": dataset.ds_meta_data.description,
            "creators": [{"name": author.name} for author in dataset.ds_meta_data.authors],
            "keywords": (
                ["uvlhub"] if not dataset.ds_meta_data.tags else dataset.ds_meta_data.tags.split(", ") + ["uvlhub"]
            ),
            "access_right": "open",
            "license": "CC-BY-4.0",
        }

        if self.is_fakenodo:
            data = {"meta": metadata}
            response = requests.post(self.ZENODO_API_URL, json=data, headers=self.headers)
        else:
            data = {"metadata": metadata}
            response = requests.post(self.ZENODO_API_URL, params=self.params, json=data, headers=self.headers)

        if response.status_code not in (200, 201):
            raise Exception(f"Failed to create deposition. Error details: {response.text}")
        return response.json()

    def upload_file(self, dataset: DataSet, deposition_id: int, feature_model: FeatureModel, user=None) -> dict:
        """
        Upload a file to a deposition in Zenodo or simulate it in Fakenodo.
        """
        uvl_filename = feature_model.fm_meta_data.uvl_filename
        user_id = current_user.id if user is None else user.id
        file_path = os.path.join(uploads_folder_name(), f"user_{str(user_id)}", f"dataset_{dataset.id}/", uvl_filename)

        if self.is_fakenodo:
            # Simulación: no existe /files en fakenodo, devolvemos respuesta simulada
            return {
                "id": deposition_id,
                "doi": f"10.9999/fakenodo.{uuid.uuid4().hex[:6]}",
                "published": True,
                "meta": {
                    "title": dataset.ds_meta_data.title,
                    "description": dataset.ds_meta_data.description,
                },
                "files": [uvl_filename],
            }

        # --- Zenodo real ---
        data = {"name": uvl_filename}
        files = {"file": open(file_path, "rb")}
        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/files"

        response = requests.post(publish_url, params=self.params, data=data, files=files)
        files["file"].close()

        if response.status_code != 201:
            error_message = f"Failed to upload files. Error details: {response.json()}"
            raise Exception(error_message)
        return response.json()

    def publish_deposition(self, deposition_id: int) -> dict:
        """
        Publish a deposition in Zenodo or Fakenodo.
        """
        if self.is_fakenodo:
            # Simulación: devolvemos directamente DOI y published
            return {
                "id": deposition_id,
                "doi": f"10.9999/fakenodo.{uuid.uuid4().hex[:6]}",
                "published": True,
            }

        # --- Zenodo real ---
        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/actions/publish"
        response = requests.post(publish_url, params=self.params, headers=self.headers)

        if response.status_code not in (200, 202):
            raise Exception(f"Failed to publish deposition. Error: {response.text}")
        return response.json()

    def get_deposition(self, deposition_id: int) -> dict:
        """
        Get a deposition from Zenodo.

        Args:
            deposition_id (int): The ID of the deposition in Zenodo.

        Returns:
            dict: The response in JSON format with the details of the deposition.
        """
        if self.is_fakenodo:
            # Simulación: devolver un depósito publicado con DOI
            return {
                "id": deposition_id,
                "doi": f"10.9999/fakenodo.{uuid.uuid4().hex[:6]}",
                "published": True,
                "meta": {"title": "Simulated dataset", "description": "Stored in fakenodo"},
            }

        deposition_url = f"{self.ZENODO_API_URL}/{deposition_id}"
        response = requests.get(deposition_url, params=self.params, headers=self.headers)
        if response.status_code != 200:
            raise Exception("Failed to get deposition")
        return response.json()

    def get_doi(self, deposition_id: int) -> str:
        """
        Get the DOI of a deposition from Zenodo.

        Args:
            deposition_id (int): The ID of the deposition in Zenodo.

        Returns:
            str: The DOI of the deposition.
        """
        return self.get_deposition(deposition_id).get("doi")