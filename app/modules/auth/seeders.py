from app.modules.auth.models import User
from app.modules.profile.models import UserProfile
from core.seeders.BaseSeeder import BaseSeeder
from app import db  # Asegúrate de tener acceso a la sesión de SQLAlchemy


class AuthSeeder(BaseSeeder):

    priority = 1  # Higher priority

    def run(self):
        # Lista de usuarios a insertar
        users_data = [
            {"email": "user1@example.com", "password": "1234", "name": "John", "surname": "Doe"},
            {"email": "user2@example.com", "password": "1234", "name": "Jane", "surname": "Doe"},
        ]

        seeded_users = []

        for user_data in users_data:
            # Revisar si el usuario ya existe
            existing_user = db.session.query(User).filter_by(email=user_data["email"]).first()
            if not existing_user:
                # Crear nuevo usuario
                new_user = User(email=user_data["email"], password=user_data["password"])
                db.session.add(new_user)
                db.session.flush()  # Para obtener el id sin hacer commit aún
                seeded_users.append(new_user)
            else:
                seeded_users.append(existing_user)

        # Crear perfiles para cada usuario, solo si no existen
        for user, user_data in zip(seeded_users, users_data):
            existing_profile = db.session.query(UserProfile).filter_by(user_id=user.id).first()
            if not existing_profile:
                profile_data = {
                    "user_id": user.id,
                    "orcid": "",
                    "affiliation": "Some University",
                    "name": user_data["name"],
                    "surname": user_data["surname"],
                }
                new_profile = UserProfile(**profile_data)
                db.session.add(new_profile)

        # Confirmar todos los cambios en la base de datos
        db.session.commit()
