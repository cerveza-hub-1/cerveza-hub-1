from datetime import datetime
from enum import Enum

from flask import request
from sqlalchemy import Enum as SQLAlchemyEnum

from app import db


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # 1. Usar 'user.id' como string para referenciar la tabla 'user' (asumiendo que User es User)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # 2. Usar 'User' como string para la relación
    author = db.relationship("User", backref="comments", foreign_keys=[author_id])

    # 3. Usar 'data_set.id' como string para la clave foránea del dataset
    dataset_id = db.Column(db.Integer, db.ForeignKey("data_set.id"), nullable=False)
    # (La relación 'data_set' se define automáticamente con el backref en DataSet)

    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # 4. Referencia de respuesta anidada usando 'Comment' como string
    comment_parent_id = db.Column(db.Integer, db.ForeignKey("comment.id"), nullable=True)
    replies = db.relationship(
        "Comment", 
        backref=db.backref("parent", remote_side=[id]), 
        lazy="dynamic", 
        cascade="all, delete"
    )
    
    is_deleted = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        # ACCESO AL PERFIL CONFIRMADO: self.author apunta al objeto User, 
        # y User.profile apunta al UserProfile (que tiene name y surname).
        author_full_name = f"{self.author.profile.name} {self.author.profile.surname}"

        return {
            "id": self.id,
            # CAMBIO CLAVE: Usa el profile para obtener el nombre completo
            "author_name": author_full_name, 
            "created_at": self.created_at.isoformat(),
            "content": self.content,
            "parent_id": self.comment_parent_id
        }