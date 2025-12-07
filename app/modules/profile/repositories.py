from app.modules.profile.models import UserProfile
from core.repositories.BaseRepository import BaseRepository


class UserProfileRepository(BaseRepository):
    def __init__(self):
        super().__init__(UserProfile)

    def get_by_user_id(self, user_id):
        """
        Devuelve el perfil asociado a un usuario específico.
        :param user_id: ID del usuario.
        :return: instancia de UserProfile o None si no existe.
        """
        return self.model.query.filter_by(user_id=user_id).first()
