from models.user_model import Usuario
import bcrypt

class ChangePasswordCommand:
    def __init__(self, user_id: str, old_password: str, new_password: str):
        self.user_id = user_id
        self.old_password = old_password
        self.new_password = new_password

    def execute(self):
        """
        Verifica la contraseña actual y actualiza a la nueva.
        Lanza una excepción si la verificación falla.
        """
        usuario = Usuario.find_by_id(self.user_id)
        
        if not usuario or not usuario.get("usuario_clave"):
            raise ValueError("Usuario no encontrado o clave no válida.")

        # Verificar contraseña actual usando bcrypt
        if not bcrypt.checkpw(self.old_password.encode('utf-8'), usuario["usuario_clave"].encode('utf-8')):
            raise ValueError("Contraseña actual incorrecta.")

        # Hashear la nueva contraseña antes de guardar
        hash_nueva = bcrypt.hashpw(self.new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Actualizar en el modelo/BD
        Usuario.update(self.user_id, {"usuario_clave": hash_nueva.decode('utf-8')})