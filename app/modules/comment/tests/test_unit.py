from app.modules.comment.services import CommentService
import pytest
from app import create_app
import app.modules.dataset.routes as dataset_routes

# ============================================================
# Mocks para Pruebas Unitarias
# ============================================================


class DummyComment:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return {
            "id": getattr(self, "id", None),
            "author_name": getattr(self, "author_name", ""),
            "created_at": getattr(self, "created_at", ""),
            "content": getattr(self, "content", ""),
            "parent_id": getattr(self, "comment_parent_id", None),
        }


class DummyRepo:
    def __init__(self):
        self.last_create_kwargs = None
        self.last_update = None
        self._store = {}

    def create(self, **kwargs):
        # Simulate SQLAlchemy model instance
        self.last_create_kwargs = kwargs
        instance = DummyComment(**kwargs)
        instance.id = 1
        # store for potential retrieval
        self._store[instance.id] = instance
        return instance

    def get_by_dataset_id(self, dataset_id):
        # Return a list of non-deleted comments for the dataset (simple simulation)
        # For testing purpose return a list with a single DummyComment
        return [DummyComment(id=1, author_id=2, dataset_id=dataset_id, content="hello", comment_parent_id=None)]

    def get_or_404(self, id):
        # Return stored comment or simulate an object with given id
        return self._store.get(id, DummyComment(id=id))

    def update(self, id, **kwargs):
        # Mark updated fields and return updated object
        self.last_update = (id, kwargs)
        obj = self._store.get(id, DummyComment(id=id))
        for k, v in kwargs.items():
            setattr(obj, k, v)
        self._store[id] = obj
        return obj

# ============================================================
# Tests Unitarios de CommentService
# ============================================================

# Prueba de creación básica de comentarios


def test_create_comment_without_parent_sets_correct_fields():

    # Verifica que la función create_comment() llama al repositorio con
    # los argumentos correctos cuando NO hay parent_id.

    repo = DummyRepo()
    svc = CommentService()
    svc.repository = repo

    comment = svc.create_comment(author_id=10, dataset_id=5, content="A test comment")

    # repository.create should have been called with comment_parent_id omitted (None not passed explicitly)
    assert repo.last_create_kwargs is not None
    assert repo.last_create_kwargs["author_id"] == 10
    assert repo.last_create_kwargs["dataset_id"] == 5
    assert repo.last_create_kwargs["content"] == "A test comment"

    # returned object has id and attributes
    assert hasattr(comment, "id") and comment.id == 1
    assert comment.content == "A test comment"


# Prueba la creación de respuestas a comentarios (comentarios hijos)


def test_create_comment_with_parent_passes_parent_id():

    # Comprueba que si se pasa parent_id, el servicio
    # lo reenvía como comment_parent_id al repositorio

    repo = DummyRepo()
    svc = CommentService()
    svc.repository = repo

    comment = svc.create_comment(author_id=11, dataset_id=6, content="Reply", parent_id=42)

    # repository.create should have received comment_parent_id argument
    assert repo.last_create_kwargs is not None
    assert repo.last_create_kwargs.get("comment_parent_id") == 42
    assert comment.content == "Reply"


# Prueba la obtención de comentarios por dataset


def test_get_comments_for_dataset_calls_repository():

    # Garantiza que se retorna una lista con
    # comentarios provenientes del repositorio que tienen el correcto dataset_id

    repo = DummyRepo()
    svc = CommentService()
    svc.repository = repo

    comments = svc.get_comments_for_dataset(123)

    assert isinstance(comments, list)
    assert len(comments) == 1
    assert comments[0].dataset_id == 123


# Prueba el borrado lógico de un comentario


def test_delete_comment_performs_soft_delete():

    # El servicio llama al método update() del repositorio, pasandole el campo is_deleted=True
    # Se comprueba que se envía correctamente al repositorio y que el objeto resultante tiene is_deleted=True

    repo = DummyRepo()
    svc = CommentService()
    svc.repository = repo

    # create a comment to have it in the repo store
    created = repo.create(author_id=2, dataset_id=7, content="to be deleted")

    result = svc.delete_comment(created.id)

    # repository.update should be called to mark is_deleted=True
    assert repo.last_update is not None
    updated_id, kwargs = repo.last_update
    assert updated_id == created.id
    assert kwargs.get("is_deleted") is True
    # result should be the updated object
    assert getattr(result, "is_deleted", True) is True


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def client(monkeypatch):
    """Crea un cliente Flask de pruebas con un usuario autenticado falso."""
    app = create_app()
    app.testing = True

    class DummyUser:
        id = 10

        @property
        def is_authenticated(self):
            return True

        @property
        def is_active(self):
            return True

        @property
        def is_anonymous(self):
            return False

        def get_id(self):
            return str(self.id)

    # Sustituir current_user por DummyUser
    monkeypatch.setattr("flask_login.utils._get_user", lambda: DummyUser())

    with app.test_client() as client:
        yield client


# ===========================================================
# Pruebas de rutas de comentarios (integración básica)
# ===========================================================


# Prueba que el endpoint lista comentarios correctamente


def test_list_comments_success(client, monkeypatch):
    """GET /dataset/<id>/comments debe devolver una lista de comentarios y un 200."""

    class DummyComment:
        def __init__(self, id, content):
            self.id = id
            self.content = content

        def to_dict(self):
            return {"id": self.id, "content": self.content}

    class StubService:
        def get_comments_for_dataset(self, dataset_id):
            return [DummyComment(1, "Hola"), DummyComment(2, "Adiós")]

    monkeypatch.setattr(dataset_routes, "comment_service", StubService())

    resp = client.get("/dataset/5/comments")
    assert resp.status_code == 200
    assert resp.get_json() == [
        {"id": 1, "content": "Hola"},
        {"id": 2, "content": "Adiós"},
    ]


# Prueba creación exitosa de comentario vía endpoint


def test_create_comment_success(client, monkeypatch):
    """POST debe crear un comentario correctamente y devolver un 201."""

    class DummyComment:
        def __init__(self, id, content):
            self.id = id
            self.content = content

        def to_dict(self):
            return {"id": self.id, "content": self.content}

    class StubService:
        def create_comment(self, **kwargs):
            return DummyComment(1, kwargs["content"])

    monkeypatch.setattr(dataset_routes, "comment_service", StubService())

    resp = client.post("/dataset/3/comments", json={"content": "Nuevo"})
    assert resp.status_code == 201
    assert resp.get_json() == {"id": 1, "content": "Nuevo"}


# Prueba validación de entrada del endpoint


def test_create_comment_missing_content(client, monkeypatch):
    """POST debe devolver 400 si el content esta vacio"""

    resp = client.post("/dataset/3/comments", json={"content": ""})
    assert resp.status_code == 400
    assert resp.get_json() == {"message": "Content is required"}


# Prueba manejo de errores del endpoint


def test_create_comment_failure(client, monkeypatch):
    """POST debe devolver 500 si el servicio falla"""

    class StubService:
        def create_comment(self, **kwargs):
            raise RuntimeError("DB error")

    monkeypatch.setattr(dataset_routes, "comment_service", StubService())

    resp = client.post("/dataset/3/comments", json={"content": "Hola"})
    assert resp.status_code == 500
    assert resp.get_json().get("message") == "Failed to create comment due to server error."


# Prueba borrado correcto cuando el usuario está autorizado


def test_delete_comment_success(client, monkeypatch):
    """DELETE debe permitir borrar comentarios cuando el usuario es autor del dataset"""

    class DummyDataset:
        user_id = 10   # mismo que current_user

    class DummyComment:
        data_set = DummyDataset()

    class StubService:
        def get_or_404(self, id):
            return DummyComment()

        def delete_comment(self, id):
            return True

    monkeypatch.setattr(dataset_routes, "comment_service", StubService())

    resp = client.delete("/comments/1")
    assert resp.status_code == 200
    assert resp.get_json() == {"message": "Comment deleted successfully"}


# Prueba restricción de permisos al borrar comentarios


def test_delete_comment_forbidden(client, monkeypatch):
    """DELETE debe devolver 403 si el usuario NO es autor del dataset."""

    class DummyDataset:
        user_id = 99  # diferente del current_user = 10

    class DummyComment:
        data_set = DummyDataset()

    class StubService:
        def get_or_404(self, id):
            return DummyComment()

    monkeypatch.setattr(dataset_routes, "comment_service", StubService())

    resp = client.delete("/comments/1")
    assert resp.status_code == 403
    assert resp.get_json().get("message").startswith("Forbidden")


# Prueba manejo de errores al borrar un comentario


def test_delete_comment_failure(client, monkeypatch):
    """DELETE debe devolver 500 si delete_comment falla."""

    class DummyDataset:
        user_id = 10  # autorizado

    class DummyComment:
        data_set = DummyDataset()

    class StubService:
        def get_or_404(self, id):
            return DummyComment()

        def delete_comment(self, id):
            raise RuntimeError("fail")

    monkeypatch.setattr(dataset_routes, "comment_service", StubService())

    resp = client.delete("/comments/1")
    assert resp.status_code == 500
    assert resp.get_json().get("message") == "Failed to delete comment"
