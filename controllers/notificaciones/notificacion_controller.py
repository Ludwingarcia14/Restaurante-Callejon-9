"""
Controller de Notificaciones - Sistema Restaurante Callejón 9
Maneja las API endpoints para notificaciones en tiempo real
"""

from flask import jsonify, session, request
from functools import wraps
from bson import ObjectId
from datetime import datetime, timedelta
from pytz import timezone
from models.notificacion import Notificacion
from services.notificaciones.notification_service import notificar_usuario
import logging

logger = logging.getLogger(__name__)

Mexico_TZ = timezone('America/Mexico_City')

def get_mexico_datetime():
    return datetime.now(Mexico_TZ)


def login_required_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario_id" not in session:
            return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return decorated_function


class NotificacionCommandHandler:
    @staticmethod
    def crear_notificacion(tipo, mensaje, id_usuario, datos_extra=None):
        try:
            nueva_notif = {
                "tipo": tipo,
                "mensaje": mensaje,
                "id_usuario": ObjectId(id_usuario),
                "leida": False,
                "fecha": get_mexico_datetime(),
                "created_at": get_mexico_datetime(),
                "updated_at": get_mexico_datetime(),
                "datos_extra": datos_extra or {}
            }
            
            result = Notificacion.create(nueva_notif)
            
            notificar_usuario(
                user_id=id_usuario,
                evento=tipo,
                mensaje=mensaje,
                datos_extra=datos_extra
            )
            
            return {
                "success": True,
                "id": str(result.inserted_id),
                "mensaje": "Notificación creada y enviada"
            }
            
        except Exception as e:
            logger.error(f"Error creando notificación: {str(e)}")
            return {
                "success": False,
                "error": "Error interno del servidor"
            }

    @staticmethod
    def marcar_como_leida(id_notificacion):
        try:
            result = Notificacion.update(
                id_notificacion,
                {"leida": True}
            )
            
            return {
                "success": result.modified_count > 0,
                "mensaje": "Notificación marcada como leída"
            }
            
        except Exception as e:
            logger.error(f"Error marcando como leída: {str(e)}")
            return {
                "success": False,
                "error": "Error interno del servidor"
            }

    @staticmethod
    def marcar_todas_leidas(id_usuario):
        try:
            result = Notificacion.marcar_todas_leidas(id_usuario)
            
            return {
                "success": True,
                "modificadas": result.modified_count,
                "mensaje": f"{result.modified_count} notificaciones marcadas como leídas"
            }
            
        except Exception as e:
            logger.error(f"Error marcando todas leídas: {str(e)}")
            return {
                "success": False,
                "error": "Error interno del servidor"
            }

    @staticmethod
    def eliminar_notificacion(id_notificacion):
        try:
            result = Notificacion.delete(id_notificacion)
            
            return {
                "success": result.deleted_count > 0,
                "mensaje": "Notificación eliminada"
            }
            
        except Exception as e:
            logger.error(f"Error eliminando notificación: {str(e)}")
            return {
                "success": False,
                "error": "Error interno del servidor"
            }


class NotificacionSistemaHandler:
    TIPOS_ADMIN = {
        "LOGIN": " Inicio de Sesión",
        "LOGOUT": " Cierre de Sesión",
        "ERROR_SISTEMA": " Error del Sistema",
        "BACKUP_CREADO": " Backup Creado",
        "BACKUP_RESTAURADO": " Backup Restaurado",
        "EMPLEADO_CREADO": " Nuevo Empleado",
        "EMPLEADO_ELIMINADO": " Empleado Eliminado",
        "ALERTA_INVENTARIO": " Alerta de Inventario"
    }

    TIPOS_MESERO = {
        "LOGIN": " Inicio de Sesión",
        "LOGOUT": " Cierre de Sesión",
        "PEDIDO_ASIGNADO": " Nuevo Pedido",
        "PEDIDO_LISTO": " Pedido Listo",
        "MESA_ASIGNADA": " Mesa Asignada",
        "PROPINA_RECIBIDA": "Propina Recibida"
    }

    TIPOS_COCINA = {
        "LOGIN": " Inicio de Sesión",
        "LOGOUT": " Cierre de Sesión",
        "PEDIDO_NUEVO": " Nuevo Pedido",
        "PEDIDO_URGENTE": " Pedido Urgente",
        "INGREDIENTE_FALTANTE": " Ingrediente Faltante"
    }

    TIPOS_INVENTARIO = {
        "LOGIN": " Inicio de Sesión",
        "LOGOUT": " Cierre de Sesión",
        "STOCK_BAJO": " Stock Bajo",
        "ENTRADA_REGISTRADA": " Entrada Registrada",
        "SALIDA_REGISTRADA": " Salida Registrada",
        "MERMA_REGISTRADA": " Merma Registrada"
    }

    @classmethod
    def notificar_login(cls, id_usuario, nombre_usuario, rol):
        from models.empleado_model import Usuario
        
        mensaje = f" {nombre_usuario} ha iniciado sesión"
        
        admins = Usuario.find_by_rol("1")
        admins_activos = [admin for admin in admins if admin.get("usuario_status") == 1]
        
        resultados = []
        for admin in admins_activos:
            resultado = NotificacionCommandHandler.crear_notificacion(
                tipo="LOGIN",
                mensaje=mensaje,
                id_usuario=str(admin["_id"]),
                datos_extra={
                    "rol": rol,
                    "usuario_id": id_usuario,
                    "nombre_usuario": nombre_usuario,
                    "timestamp": get_mexico_datetime().isoformat()
                }
            )
            resultados.append(resultado)
        
        return {
            "success": any(r.get("success") for r in resultados),
            "notificaciones_enviadas": len(resultados)
        }

    @classmethod
    def notificar_logout(cls, id_usuario, nombre_usuario, rol):
        from models.empleado_model import Usuario
        
        mensaje = f"🚪 {nombre_usuario} ha cerrado sesión"
        
        admins = Usuario.find_by_rol("1")
        admins_activos = [admin for admin in admins if admin.get("usuario_status") == 1]
        
        resultados = []
        for admin in admins_activos:
            resultado = NotificacionCommandHandler.crear_notificacion(
                tipo="LOGOUT",
                mensaje=mensaje,
                id_usuario=str(admin["_id"]),
                datos_extra={
                    "rol": rol,
                    "usuario_id": id_usuario,
                    "nombre_usuario": nombre_usuario,
                    "timestamp": get_mexico_datetime().isoformat()
                }
            )
            resultados.append(resultado)
        
        return {
            "success": any(r.get("success") for r in resultados),
            "notificaciones_enviadas": len(resultados)
        }

    @classmethod
    def notificar_error(cls, id_usuario, tipo_error, descripcion):
        mensaje = f"Error: {descripcion}"
        
        return NotificacionCommandHandler.crear_notificacion(
            tipo="ERROR_SISTEMA",
            mensaje=mensaje,
            id_usuario=id_usuario,
            datos_extra={
                "tipo_error": tipo_error,
                "timestamp": get_mexico_datetime().isoformat()
            }
        )

    @classmethod
    def notificar_backup(cls, id_usuario, tipo_backup, nombre_archivo):
        tipo = "BACKUP_CREADO" if tipo_backup == "crear" else "BACKUP_RESTAURADO"
        mensaje = f"Backup {tipo_backup}: {nombre_archivo}"
        
        return NotificacionCommandHandler.crear_notificacion(
            tipo=tipo,
            mensaje=mensaje,
            id_usuario=id_usuario,
            datos_extra={
                "archivo": nombre_archivo,
                "timestamp": get_mexico_datetime().isoformat()
            }
        )

    @classmethod
    def notificar_empleado(cls, id_admin, accion, nombre_empleado):
        tipo = "EMPLEADO_CREADO" if accion == "crear" else "EMPLEADO_ELIMINADO"
        mensaje = f"Empleado {accion}: {nombre_empleado}"
        
        return NotificacionCommandHandler.crear_notificacion(
            tipo=tipo,
            mensaje=mensaje,
            id_usuario=id_admin,
            datos_extra={
                "empleado": nombre_empleado,
                "timestamp": get_mexico_datetime().isoformat()
            }
        )

    @classmethod
    def notificar_inventario(cls, id_usuario, tipo_movimiento, nombre_insumo, cantidad):
        tipos = {
            "entrada": "ENTRADA_REGISTRADA",
            "salida": "SALIDA_REGISTRADA",
            "merma": "MERMA_REGISTRADA",
            "stock_bajo": "STOCK_BAJO"
        }
        
        tipo = tipos.get(tipo_movimiento, "STOCK_BAJO")
        mensaje = f"{tipo_movimiento.title()}: {nombre_insumo} - {cantidad} unidades"
        
        return NotificacionCommandHandler.crear_notificacion(
            tipo=tipo,
            mensaje=mensaje,
            id_usuario=id_usuario,
            datos_extra={
                "insumo": nombre_insumo,
                "cantidad": cantidad,
                "timestamp": get_mexico_datetime().isoformat()
            }
        )


class NotificacionController:
    """
    Controlador principal de notificaciones
    """

    @staticmethod
    @staticmethod
    @login_required_api
    def get_notificaciones():
        """
        GET /api/notificaciones
        Obtiene todas las notificaciones del usuario autenticado
        """
        try:
            usuario_id = session.get("usuario_id")
            
            notificaciones = list(Notificacion.collection.find(
                {"id_usuario": ObjectId(usuario_id)}
            ).sort("fecha", -1))
            
            for n in notificaciones:
                n["_id"] = str(n["_id"])
                n["id_usuario"] = str(n["id_usuario"])
                if n.get("fecha"):
                    n["fecha"] = n["fecha"].isoformat()
            
            return jsonify({
                "success": True,
                "notificaciones": notificaciones,
                "total": len(notificaciones)
            }), 200
            
        except Exception as e:
            logger.error(f"Error en get_notificaciones: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Error interno del servidor"
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
            logger.error(f"Error en get_notificaciones: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Error interno del servidor"
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
            logger.error(f"Error en get_notificaciones: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Error interno del servidor"
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
            logger.error(f"Error en get_notificaciones: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Error interno del servidor"
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
            logger.error(f"Error en get_notificaciones: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Error interno del servidor"
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
            logger.error(f"Error en get_notificaciones: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Error interno del servidor"
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
                "exp": get_mexico_datetime() + timedelta(hours=24)
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
            logger.error(f"Error en get_notificaciones: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Error interno del servidor"
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