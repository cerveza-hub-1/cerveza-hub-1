from app import db


class Fakenodo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meta = db.Column(db.JSON)  # ← este campo debe existir
    doi = db.Column(db.String(255))
    published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)

    def __repr__(self):
        return f"Fakenodo<{self.id}>"
