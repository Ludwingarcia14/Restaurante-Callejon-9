import bcrypt
from typing import Optional

class PasswordService:
    """
    Servicio encargado del hasheo y verificación de contraseñas.
    Utiliza bcrypt para una seguridad robusta.
    """
    
    # Costo recomendado para bcrypt. Ajustar si el hardware es muy limitado.
    BCRYPT_ROUNDS = 12 

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Genera el hash de una contraseña dada.

        Args:
            password: La contraseña en texto plano (string).

        Returns:
            str: El hash generado, codificado como string UTF-8.
        """
        if not password:
            raise ValueError("La contraseña no puede estar vacía.")
            
        # 1. Codificar la contraseña a bytes
        password_bytes = password.encode('utf-8')
        
        # 2. Generar el salt (sal) y hashear en una sola operación
        salt = bcrypt.gensalt(rounds=PasswordService.BCRYPT_ROUNDS)
        hashed_bytes = bcrypt.hashpw(password_bytes, salt)
        
        # 3. Decodificar a string para guardar en la base de datos (MongoDB)
        return hashed_bytes.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verifica si una contraseña dada coincide con un hash existente.

        Args:
            password: La contraseña en texto plano (string).
            hashed_password: El hash almacenado en la base de datos (string).

        Returns:
            bool: True si coinciden, False en caso contrario.
        """
        if not password or not hashed_password:
            return False
            
        try:
            # bcrypt.checkpw trabaja con bytes, por lo que codificamos ambos
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except ValueError:
            # Esto puede ocurrir si el hash_password no tiene el formato bcrypt correcto
            return False
        except Exception:
            return False