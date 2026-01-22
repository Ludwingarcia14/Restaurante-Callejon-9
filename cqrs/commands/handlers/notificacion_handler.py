# cqrs/commands/handlers/notificacion_handler.py

import requests
import os
import datetime
from ..models.notificar_command import NotificarUsuarioCommand

# Simula la lectura de la URL del servicio Socket IO/Node.js
SOCKET_SERVICE_URL = os.environ.get('SOCKET_SERVICE_URL', 'http://localhost:3000/api/socket/notify')

class NotificacionCommandHandler:
    @staticmethod
    def handle(command: NotificarUsuarioCommand, Notificacion_Model):
        """
        Maneja el comando de crear y enviar una notificación.
        Notificacion_Model es el modelo (ORM/ODM) inyectado desde la capa superior.
        """
        
        # 1️⃣ Persistencia (Escribir)
        nueva_notificacion_data = {
            "tipo": command.tipo,
            "mensaje": command.mensaje,
            "id_usuario": command.id_usuario, 
            "leida": False, # Estado inicial
            "fecha": datetime.datetime.utcnow()
        }
        
        # Guardar en Mongo (asumiendo que Notificacion_Model.create inserta y devuelve el objeto guardado)
        # Nota: La implementación exacta de .create depende de tu modelo.
        try:
            registro_guardado = Notificacion_Model.create(nueva_notificacion_data) 
        except Exception as e:
            print(f"[ERROR PERSISTENCIA] Falló al guardar notificación: {e}")
            # Devolvemos un error si la persistencia falla
            raise Exception("Error al guardar la notificación en la base de datos.")

        # 2️⃣ Comunicación Externa (Efecto Secundario)
        try:
            requests.post(
                SOCKET_SERVICE_URL,
                json={
                    "target": f"room_{command.id_usuario}",
                    "evento": "notificacion",
                    "data": {
                        "mensaje": command.mensaje,
                        "tipo": command.tipo
                    }
                },
                timeout=5 # Tiempo de espera para la solicitud al socket
            )
        except requests.exceptions.RequestException as e:
            # Capturamos el error de la solicitud HTTP, pero no impedimos el retorno exitoso
            print(f"[ADVERTENCIA SOCKET] No se pudo enviar a Node.js: {e}") 

        # Devolver el resultado de la operación
        # Se puede devolver solo la parte que interesa al cliente o el objeto guardado
        return {"ok": True, "msg": "Notificación guardada y enviada", "data": registro_guardado.to_dict()}