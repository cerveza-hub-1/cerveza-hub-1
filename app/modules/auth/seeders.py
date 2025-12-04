from app.modules.auth.models import User
from app.modules.profile.models import UserProfile
from core.seeders.BaseSeeder import BaseSeeder


class AuthSeeder(BaseSeeder):

    priority = 1  # Higher priority

    def run(self):
        # Usuarios a crear
        users_to_create = [
            {"email": "user1@example.com", "password": "1234", "name": "John", "surname": "Doe"},
            {"email": "user2@example.com", "password": "1234", "name": "Jane", "surname": "Doe"},
        ]

        for u in users_to_create:
            # Solo crear si no existe
            user = User.query.filter_by(email=u["email"]).first()
            if not user:
                user = User(email=u["email"], password=u["password"])
                self.seed([user])

            # Crear perfil si no existe
            profile = UserProfile.query.filter_by(user_id=user.id).first()
            if not profile:
                profile = UserProfile(
                    user_id=user.id, orcid="", affiliation="Some University", name=u["name"], surname=u["surname"]
                )
                self.seed([profile])
