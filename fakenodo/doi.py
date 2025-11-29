import uuid


def new_id() -> str:
    return str(uuid.uuid4())


def short_id(full_id: str) -> str:
    return full_id[:8]


def root_doi(entity_id: str) -> str:
    return f"10.1234/fakenodo.{short_id(entity_id)}"


def versioned_doi(root: str, version_index: int) -> str:
    return root if version_index == 0 else f"{root}.{version_index}"
