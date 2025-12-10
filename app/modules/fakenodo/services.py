import logging
import os

from app.modules.fakenodo.repositories import FakenodoRepository
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


class FakenodoService(BaseService):
    def __init__(self):
        super().__init__(FakenodoRepository())
        self.FAKENODO_URL = os.getenv(
            "FAKENODO_URL", "http://localhost:5000/fakenodo/api/records"
        )

    def create_record(self, metadata: dict) -> dict:
        record = self.repository.create(meta=metadata)
        return self.get_record(record.id)

    def publish_record(self, record_id: int, files: list[str]) -> dict:
        record = self.repository.get_or_404(record_id)

        if not isinstance(files, list):
            files = []

        new_version = record.add_version(meta=record.meta, files=files, published=True)
        return new_version

    def list_versions(self, record_id: int) -> list[dict]:
        record = self.repository.get_or_404(record_id)
        return record.versions

    def get_record(self, record_id: int) -> dict:
        record = self.repository.get_or_404(record_id)
        latest = record.versions[-1]

        # Recoger archivos de TODAS las versiones
        all_files = []
        for version in record.versions:
            version_files = version.get("files", [])
            if isinstance(version_files, list):
                all_files.extend(version_files)

        # Eliminar duplicados
        unique_files = list(set([f for f in all_files if f]))

        return {
            "id": record.id,
            "doi": latest["doi"],
            "published": latest["published"],
            "metadata": latest["meta"],
            "files": unique_files,  # ← ESTO ES IMPORTANTE
            "versions": record.versions,
        }

    def list_all(self):
        return self.repository.list_all()
