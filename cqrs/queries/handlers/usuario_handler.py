# cqrs/queries/handlers/usuario_handler.py

import jwt
import datetime
from bson import ObjectId

class UsuarioQueryHandler:
    def __init__(self, db_accessor, app_config):
        self.db = db_accessor
        # Obtiene el secreto desde la configuración inyectada
        self.socket_jwt_secret = app_config.get('SOCKET_JWT_SECRET')
        self.jwt_algorithm = 'HS256'

    def get_user_data_and_token(self, user_id_str: str, session_data: dict):
        """Valida el rol del usuario en la BD y genera un JWT para Socket IO."""
        
        tipo_detectado = None
        
        try:
            query_id = ObjectId(user_id_str)
        except:
            query_id = user_id_str 

        # --- Consulta la base de datos (Lógica de Rol/Acceso) ---
        cliente = self.db.clientes.find_one({"_id": query_id})
        if cliente and cliente.get('cliente_rol') == 4:
            tipo_detectado = 'cliente'
        
        if not tipo_detectado:
            usuario = self.db.usuarios.find_one({"_id": query_id})
            if usuario and usuario.get('usuario_rol') == "3":
                tipo_detectado = 'asesor'
        
        if not tipo_detectado:
            tipo_detectado = session_data.get('usuario_tipo', 'usuario_generico')

        # --- Generar Token JWT ---
        payload = {
            'id': user_id_str, 
            'tipo': tipo_detectado,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        
        socket_token = jwt.encode(
            payload, 
            self.socket_jwt_secret, 
            algorithm=self.jwt_algorithm
        )
        
        if isinstance(socket_token, bytes):
            socket_token = socket_token.decode('utf-8')
            
        return {'socket_token': socket_token}