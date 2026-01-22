# controllers/api/cqrs/commands/auth/handlers/login_status_handler.py

import secrets
from bson import ObjectId

class LoginStatusHandler:
    @staticmethod
    def handle(user_id_str, user_type, user_model, client_model):
        """Actualiza el status a ONLINE (1) y genera token de sesión para el login."""
        
        token_session = secrets.token_urlsafe(32)
        # user_id = ObjectId(user_id_str) # El modelo de DB debería manejar la conversión si es necesario

        if user_type == "usuario":
            user_model.update(user_id_str, {"usuario_tokensession": token_session, "usuario_status": 1})
        elif user_type == "cliente":
            client_model.update(user_id_str, {"cliente_tokensession": token_session, "cliente_status": 1})
        
        return token_session # Devuelve el token para que el controlador lo use en la sesión de Flask