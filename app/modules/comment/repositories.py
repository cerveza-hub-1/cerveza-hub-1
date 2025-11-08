from app.modules.comment.models import Comment
from core.repositories.BaseRepository import BaseRepository


class CommentRepository(BaseRepository):
    def __init__(self):
        super().__init__(Comment)

    def get_by_dataset_id(self, dataset_id: int) -> list[Comment]:
        # Obtiene solo comentarios principales (sin parent_id)
        return (
            self.model.query.filter_by(dataset_id=dataset_id, comment_parent_id=None, is_deleted=False)
            .order_by(self.model.created_at.desc())
            .all()
        )
