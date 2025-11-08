from typing import Optional

from app.modules.comment.models import Comment
from app.modules.comment.repositories import CommentRepository
from core.services.BaseService import BaseService


class CommentService(BaseService):
    def __init__(self):
        super().__init__(CommentRepository())

    def get_comments_for_dataset(self, dataset_id: int) -> list[Comment]:
        return self.repository.get_by_dataset_id(dataset_id)

    def create_comment(self, author_id: int, dataset_id: int, content: str, parent_id: Optional[int] = None) -> Comment:
        return self.create(author_id=author_id, dataset_id=dataset_id, content=content, comment_parent_id=parent_id)

    def delete_comment(self, comment_id: int):
        # Implementación de 'moderación' suave (soft delete)
        comment = self.repository.get_or_404(comment_id)
        return self.repository.update(comment.id, is_deleted=True)
