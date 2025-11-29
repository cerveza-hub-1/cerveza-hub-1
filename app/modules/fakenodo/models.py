class Fakenodo:
    def __init__(self, id, meta, created_at=None):
        self.id = id
        self.meta = meta
        self.created_at = created_at
        self.versions = []  # lista de dicts con {doi, meta, published, files}

    def add_version(self, meta, files=None, published=False):
        import uuid

        doi = f"10.9999/fakenodo.{uuid.uuid4().hex[:6]}" if published else None
        version = {
            "doi": doi,
            "meta": meta,
            "published": published,
            "files": files or [],
            "created_at": self.created_at,
        }
        self.versions.append(version)
        return version

    def to_dict(self):
        return {
            "id": self.id,
            "meta": self.meta,
            "versions": self.versions,
        }
