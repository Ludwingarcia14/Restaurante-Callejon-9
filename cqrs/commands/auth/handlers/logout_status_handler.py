# controllers/api/cqrs/commands/auth/handlers/logout_status_handler.py

class LogoutStatusHandler:
    @staticmethod
    def handle(user_id_str, user_type, user_model, client_model):
        """Actualiza el status a OFFLINE (0) y limpia el token de sesión para el logout."""
        
        if user_type == "usuario":
            user_model.update(user_id_str, {"usuario_status": 0, "usuario_tokensession": None})
            return True
        elif user_type == "cliente":
            client_model.update(user_id_str, {"cliente_status": 0, "cliente_tokensession": None})
            return True
        return False