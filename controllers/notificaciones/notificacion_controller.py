"""
Controller de Notificaciones - Sistema Restaurante Callejón 9
Maneja las API endpoints para notificaciones en tiempo real
"""

from flask import jsonify, session, request
from functools import wraps
from bson import ObjectId
from cqrs.queries.handlers.notificacion_query_handler import NotificacionQueryHandler
from cqrs.commands.handlers.notificacion_handler import (
    NotificacionCommandHandler,
    NotificacionSistemaHandler
)
from models.notificacion import Notificacion


def login_required_api(f):
    """Decorador para verificar autenticación en APIs"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario_id" not in session:
            return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return decorated_function


class NotificacionController:
    """
    Controlador principal de notificaciones
    """

    @staticmethod
    @login_required_api
    def get_notificaciones():
        """
        GET /api/notificaciones
        Obtiene todas las notificaciones del usuario autenticado
        """
        try:
            usuario_id = session.get("usuario_id")
            
            notificaciones = NotificacionQueryHandler.get_notificaciones(
                id_usuario_str=usuario_id,
                Notificacion_Model=Notificacion.collection
            )
            
            return jsonify({
                "success": True,
                "notificaciones": notificaciones,
                "total": len(notificaciones)
            }), 200
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @staticmethod
    @login_required_api
    def get_notificaciones_no_leidas():
        """
        GET /api/notificaciones/no-leidas
        Obtiene solo las notificaciones no leídas
        """
        try:
            usuario_id = session.get("usuario_id")
            
            notificaciones = list(Notificacion.collection.find(
                {
                    "id_usuario": ObjectId(usuario_id),
                    "leida": False
                }
            ).sort("fecha", -1))
            
            # Serializar
            for n in notificaciones:
                n["_id"] = str(n["_id"])
                n["id_usuario"] = str(n["id_usuario"])
                if n.get("fecha"):
                    n["fecha"] = n["fecha"].isoformat()
            
            return jsonify({
                "success": True,
                "notificaciones": notificaciones,
                "count": len(notificaciones)
            }), 200
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @staticmethod
    @login_required_api
    def marcar_leida(id_notificacion):
        """
        PUT /api/notificaciones/<id>/leida
        Marca una notificación como leída
        """
        try:
            result = NotificacionCommandHandler.marcar_como_leida(id_notificacion)
            
            if result["success"]:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
                
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @staticmethod
    @login_required_api
    def marcar_todas_leidas():
        """
        POST /api/notificaciones/marcar-todas-leidas
        Marca todas las notificaciones del usuario como leídas
        """
        try:
            usuario_id = session.get("usuario_id")
            
            result = NotificacionCommandHandler.marcar_todas_leidas(usuario_id)
            
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @staticmethod
    @login_required_api
    def eliminar_notificacion(id_notificacion):
        """
        DELETE /api/notificaciones/<id>
        Elimina una notificación específica
        """
        try:
            result = NotificacionCommandHandler.eliminar_notificacion(id_notificacion)
            
            if result["success"]:
                return jsonify(result), 200
            else:
                return jsonify(result), 404
                
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @staticmethod
    @login_required_api
    def get_contador():
        """
        GET /api/notificaciones/contador
        Obtiene el número de notificaciones no leídas
        """
        try:
            usuario_id = session.get("usuario_id")
            
            count = Notificacion.collection.count_documents({
                "id_usuario": ObjectId(usuario_id),
                "leida": False
            })
            
            return jsonify({
                "success": True,
                "count": count
            }), 200
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @staticmethod
    @login_required_api
    def get_datos_socket():
        """
        GET /api/me
        Obtiene datos del usuario para conexión Socket.IO
        """
        try:
            import jwt
            from datetime import datetime, timedelta
            import os
            
            usuario_id = session.get("usuario_id")
            usuario_nombre = session.get("usuario_nombre", "Usuario")
            usuario_rol = session.get("usuario_rol")
            
            # Generar token JWT para Socket.IO
            secret_key = os.getenv("JWT_SECRET_KEY", "tu_clave_secreta_super_segura")
            
            payload = {
                "usuario_id": usuario_id,
                "nombre": usuario_nombre,
                "rol": usuario_rol,
                "exp": datetime.utcnow() + timedelta(hours=24)
            }
            
            socket_token = jwt.encode(payload, secret_key, algorithm="HS256")
            
            return jsonify({
                "success": True,
                "usuario_id": usuario_id,
                "nombre": usuario_nombre,
                "rol": usuario_rol,
                "socket_token": socket_token
            }), 200
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


class NotificacionSistemaController:
    """
    Controlador para notificaciones del sistema
    Usado internamente por otros controladores
    """

    @staticmethod
    def notificar_login(usuario_id, nombre_usuario, rol):
        """Registra y notifica inicio de sesión"""
        return NotificacionSistemaHandler.notificar_login(
            id_usuario=usuario_id,
            nombre_usuario=nombre_usuario,
            rol=rol
        )

    @staticmethod
    def notificar_logout(usuario_id, nombre_usuario, rol):
        """Registra y notifica cierre de sesión"""
        return NotificacionSistemaHandler.notificar_logout(
            id_usuario=usuario_id,
            nombre_usuario=nombre_usuario,
            rol=rol
        )

    @staticmethod
    def notificar_backup_creado(usuario_id, nombre_archivo):
        """Notifica creación de backup"""
        return NotificacionSistemaHandler.notificar_backup(
            id_usuario=usuario_id,
            tipo_backup="crear",
            nombre_archivo=nombre_archivo
        )

    @staticmethod
    def notificar_backup_restaurado(usuario_id, nombre_archivo):
        """Notifica restauración de backup"""
        return NotificacionSistemaHandler.notificar_backup(
            id_usuario=usuario_id,
            tipo_backup="restaurar",
            nombre_archivo=nombre_archivo
        )

    @staticmethod
    def notificar_error(usuario_id, tipo_error, descripcion):
        """Notifica un error del sistema"""
        return NotificacionSistemaHandler.notificar_error(
            id_usuario=usuario_id,
            tipo_error=tipo_error,
            descripcion=descripcion
        )

    @staticmethod
    def notificar_empleado_creado(admin_id, nombre_empleado):
        """Notifica creación de empleado"""
        return NotificacionSistemaHandler.notificar_empleado(
            id_admin=admin_id,
            accion="crear",
            nombre_empleado=nombre_empleado
        )

    @staticmethod
    def notificar_movimiento_inventario(usuario_id, tipo_movimiento, nombre_insumo, cantidad):
        """Notifica movimiento de inventario"""
        return NotificacionSistemaHandler.notificar_inventario(
            id_usuario=usuario_id,
            tipo_movimiento=tipo_movimiento,
            nombre_insumo=nombre_insumo,
            cantidad=cantidad
        )