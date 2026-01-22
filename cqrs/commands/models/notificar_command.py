class NotificarUsuarioCommand:
    """DTO (Data Transfer Object) para el comando NotificarUsuario."""
    
    def __init__(self, id_usuario: str, mensaje: str, tipo: str = "general"):
        """
        Inicializa el comando.
        :param id_usuario: ID del usuario a notificar (string).
        :param mensaje: Contenido del mensaje.
        :param tipo: Tipo de notificación (ej. 'general', 'alerta').
        """
        self.id_usuario = id_usuario
        self.mensaje = mensaje
        self.tipo = tipo

    def to_dict(self):
        """Devuelve el comando como un diccionario útil para persistencia."""
        return {
            "id_usuario": self.id_usuario,
            "mensaje": self.mensaje,
            "tipo": self.tipo
        }