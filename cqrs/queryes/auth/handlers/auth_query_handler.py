# controllers/api/cqrs/queries/auth/handlers/auth_query_handler.py

import bcrypt

class AuthQueryHandler:
    @staticmethod
    def authenticate(email, password, user_model, client_model):
        """
        Busca al usuario/cliente por email, verifica el status y valida la contraseña.
        Retorna (usuario_doc, user_type, errors_list).
        """
        errors = []
        authenticated_user = None
        user_type = None

        # 1. Buscar en ambas colecciones (User/Cliente)
        user_doc = user_model.find_by_email(email)
        if user_doc:
            authenticated_user = user_doc
            user_type = "usuario"
        else:
            client_doc = client_model.find_by_email(email)
            if client_doc:
                authenticated_user = client_doc
                user_type = "cliente"
        
        if not authenticated_user:
            errors.append("Credenciales incorrectas")
            return None, None, errors
        
        # 2. Determinar campos y validar status
        if user_type == "usuario":
            status_field = "usuario_status"
            clave_field = "usuario_clave"
        else:
            status_field = "cliente_status"
            clave_field = "cliente_clave"

        if str(authenticated_user.get(status_field)) == "1":
            errors.append("La cuenta está siendo usada actualmente. Cierra la sesión anterior antes de ingresar.")
            return None, None, errors

        # 3. Validar Contraseña (bcrypt)
        stored_hash = authenticated_user.get(clave_field)
        if not stored_hash:
            errors.append("Este usuario no tiene contraseña configurada")
        else:
            try:
                stored_hash_bytes = stored_hash.encode("utf-8") if isinstance(stored_hash, str) else stored_hash
                password_bytes = password.encode("utf-8")
                if not bcrypt.checkpw(password_bytes, stored_hash_bytes):
                    errors.append("Credenciales incorrectas")
            except Exception:
                errors.append("Error interno al verificar la contraseña")

        if errors:
            return None, None, errors
        
        # Si todo es exitoso
        return authenticated_user, user_type, []