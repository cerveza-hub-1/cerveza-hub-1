import logging
import os
import uuid
from datetime import datetime, timezone

from flask import Response, jsonify

from app.modules.fakenodo.repositories import FakenodoRepository
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


class FakenodoService(BaseService):
    def __init__(self):
        super().__init__(FakenodoRepository())
        self.FAKENODO_URL = os.getenv("FAKENODO_URL", "http://localhost:5000")

    def test_full_connection(self) -> Response:
        success = True
        messages = []

        # Simula creación
        metadata = {
            "title": "Test Deposition",
            "description": "Simulated deposition",
            "creators": [{"name": "John Doe"}],
        }

        record = self.repository.create(
            {"meta": metadata, "doi": None, "published": False, "created_at": datetime.now(timezone.utc)}
        )

        if not record:
            success = False
            messages.append("Failed to create simulated deposition.")
            return jsonify({"success": success, "messages": messages})

        # Simula publicación con archivo
        record.doi = f"10.9999/fakenodo.{uuid.uuid4().hex[:6]}"
        record.published = True

        messages.append("Simulated publication successful.")

        return jsonify({"success": success, "messages": messages})

    def create_record(self, metadata: dict) -> dict:
        record = self.repository.create(meta=metadata)
        return record.to_dict()

    def publish_record(self, record_id: int, files: list[str]) -> dict:
        record = self.repository.get_or_404(record_id)
        new_version = record.add_version(meta=record.meta, files=files, published=True)
        return new_version

    def list_versions(self, record_id: int) -> list[dict]:
        record = self.repository.get_or_404(record_id)
        return record.versions
