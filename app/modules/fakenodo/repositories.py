from datetime import datetime
from app.modules.fakenodo.models import Fakenodo


class FakenodoRepository:
    def __init__(self):
        # almacenamiento en memoria
        self._records = {}
        self._counter = 1

    def create(self, meta, doi=None, published=False, created_at=None):
        record = Fakenodo(
            id=self._counter,
            meta=meta,
            doi=doi,
            published=published,
            created_at=created_at or datetime.utcnow()
        )
        self._records[self._counter] = record
        self._counter += 1
        return record

    def update(self, record_id, **kwargs):
        record = self._records.get(record_id)
        if not record:
            raise KeyError(f"Record {record_id} not found")
        for k, v in kwargs.items():
            setattr(record, k, v)
        return record

    def get_or_404(self, record_id):
        record = self._records.get(int(record_id))
        if not record:
            raise KeyError(f"Record {record_id} not found")
        return record

    def list_all(self):
        return [r.to_dict() for r in self._records.values()]
