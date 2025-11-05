from app import db
from cryptography.fernet import Fernet
import os

# ¡¡¡¡ Generación de clave de seguridad, se genera una sola vez !!!!
FERNET_KEY = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    raise ValueError("Missing FERNET_KEY in environment variables")

fernet = Fernet(FERNET_KEY)


class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)

    orcid = db.Column(db.String(19))
    affiliation = db.Column(db.String(100))
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)

    # Campos para 2FA
    twofa_enabled = db.Column(db.Boolean, default=False)
    twofa_secret = db.Column(db.Text, nullable=True)
    twofa_confirmed = db.Column(db.Boolean, default=False)

    # Métodos para cifrar/descifrar el código secreto
    def set_twofa_secret(self, secret: str):
        self.twofa_secret = fernet.encrypt(secret.encode()).decode()

    def get_twofa_secret(self):
        if not self.twofa_secret:
            return None
        return fernet.decrypt(self.twofa_secret.encode()).decode()

    def save(self):
        if not self.id:
            db.session.add(self)
        db.session.commit()
