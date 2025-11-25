class Fakenodo:
    def __init__(self, id, meta, doi=None, published=False, created_at=None):
        self.id = id
        self.meta = meta
        self.doi = doi
        self.published = published
        self.created_at = created_at

    def to_dict(self):
        return {
            "id": self.id,
            "meta": self.meta,
            "doi": self.doi,
            "published": self.published,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
