from app import db
from app.modules.auth.models import User
from app.modules.auth.seeders import AuthSeeder
from app.modules.profile.models import UserProfile


def test_seeder_run_creates_users_and_profiles(clean_database, test_client):
    """
    Verifica el path de creación inicial: if not user y if not profile (Seeder.run completo).
    """
    with test_client.application.app_context():
        seeder = AuthSeeder()
        seeder.run()

        # Comprobar que los 2 usuarios y 2 perfiles de users_to_create se crearon
        assert User.query.count() == 2
        assert UserProfile.query.count() == 2

        user1 = User.query.filter_by(email="user1@example.com").first()
        assert user1 is not None
        assert user1.profile.name == "John"


def test_seeder_skips_user_but_creates_profile(clean_database, test_client):
    """
    Simula el caso en que el usuario ya existe, pero el perfil no.
    (if not user es False, if not profile es True)
    """
    with test_client.application.app_context():
        # 1. Crear manualmente un solo usuario de la lista users_to_create
        user_data = {"email": "user1@example.com", "password": "1234"}
        
        user = User(**user_data)
        user.set_password(user_data["password"])
        db.session.add(user)
        db.session.commit()
        
        initial_user_count = User.query.count()
        
        # 2. Ejecutar el seeder (debe crear el perfil de user1 y el user2 + perfil2)
        seeder = AuthSeeder()
        seeder.run()

        # El usuario existente (user1) no debe duplicarse (count debe ser 2, ya que user2 se crea)
        assert User.query.count() == 2 
        assert UserProfile.query.count() == 2 

        user1 = User.query.filter_by(email="user1@example.com").first()
        assert user1.profile is not None
        assert user1.profile.name == "John"


def test_seeder_skips_both_user_and_profile(clean_database, test_client):
    """
    Simula el caso en que el usuario y el perfil ya existen.
    (if not user es False, if not profile es False)
    """
    with test_client.application.app_context():
        # 1. Crear manualmente el usuario y el perfil completo
        user_data = {"email": "user1@example.com", "password": "1234"}
        user = User(**user_data)
        user.set_password(user_data["password"])
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(
            user_id=user.id, orcid="1111", affiliation="Old Uni", name="Old John", surname="Old Doe"
        )
        db.session.add(profile)
        db.session.commit()
        
        # 2. Ejecutar el seeder (debe crear solo el user2 y su perfil)
        seeder = AuthSeeder()
        seeder.run()

        # El conteo debe subir en 1 usuario (user2) y 1 perfil (profile2)
        assert User.query.count() == 2
        assert UserProfile.query.count() == 2

        # Verificar que el perfil existente NO fue modificado
        user1 = User.query.filter_by(email="user1@example.com").first()
        assert user1.profile.name == "Old John"
