from datetime import datetime

from app import db


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Referencia al autor del comentario
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    author = db.relationship("User", backref="comments", foreign_keys=[author_id])

    # Referencia al dataset asociado
    dataset_id = db.Column(db.Integer, db.ForeignKey("data_set.id"), nullable=False)

    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Soporte para comentarios anidados
    comment_parent_id = db.Column(db.Integer, db.ForeignKey("comment.id"), nullable=True)
    replies = db.relationship(
        "Comment",
        backref=db.backref("parent", remote_side=[id]),
        lazy="dynamic",
        cascade="all, delete",
    )

    is_deleted = db.Column(db.Boolean, default=False)

    def to_dict(self):
        """Devuelve una representación del comentario en formato diccionario."""
        author_full_name = f"{self.author.profile.name} {self.author.profile.surname}"

        return {
            "id": self.id,
            "author_name": author_full_name,
            "created_at": self.created_at.isoformat(),
            "content": self.content,
            "parent_id": self.comment_parent_id,
        }
