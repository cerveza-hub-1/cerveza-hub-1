from datetime import datetime, timezone

from app.modules.fakenodo.models import Fakenodo


class FakenodoRepository:
    def __init__(self):
        self._records = {}
        self._counter = 1

    def create(self, meta):
        record = Fakenodo(id=self._counter, meta=meta, created_at=datetime.now(timezone.utc))
        # primera versión sin publicar
        record.add_version(meta, published=False)
        self._records[self._counter] = record
        self._counter += 1
        return record

    def get_or_404(self, record_id):
        record = self._records.get(int(record_id))
        if not record:
            raise KeyError(f"Record {record_id} not found")
        return record

    def list_all(self):
        return [r.to_dict() for r in self._records.values()]
