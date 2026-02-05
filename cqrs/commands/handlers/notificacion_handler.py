"""
Handler de Comandos - Notificaciones Sistema Restaurante
Gestiona la creación y actualización de notificaciones
"""

from datetime import datetime
from bson import ObjectId
from models.notificacion import Notificacion
from services.notificaciones.notification_service import notificar_usuario


class NotificacionCommandHandler:
    """
    Handler para procesar comandos relacionados con notificaciones
    """

    @staticmethod
    def crear_notificacion(tipo, mensaje, id_usuario, datos_extra=None):
        """
        Crea una nueva notificación en la BD y envía push en tiempo real
        
        Args:
            tipo: Tipo de notificación (LOGIN, LOGOUT, ERROR, BACKUP, etc.)
            mensaje: Mensaje descriptivo
            id_usuario: ID del usuario destinatario
            datos_extra: Datos adicionales opcionales
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # 1. Crear notificación en BD
            nueva_notif = {
                "tipo": tipo,
                "mensaje": mensaje,
                "id_usuario": ObjectId(id_usuario),
                "leida": False,
                "fecha": datetime.utcnow(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "datos_extra": datos_extra or {}
            }
            
            result = Notificacion.create(nueva_notif)
            
            # 2. Enviar notificación push en tiempo real
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
            print(f"❌ Error creando notificación: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def marcar_como_leida(id_notificacion):
        """
        Marca una notificación como leída
        
        Args:
            id_notificacion: ID de la notificación
            
        Returns:
            dict: Resultado de la operación
        """
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
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def marcar_todas_leidas(id_usuario):
        """
        Marca todas las notificaciones de un usuario como leídas
        
        Args:
            id_usuario: ID del usuario
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            result = Notificacion.marcar_todas_leidas(id_usuario)
            
            return {
                "success": True,
                "modificadas": result.modified_count,
                "mensaje": f"{result.modified_count} notificaciones marcadas como leídas"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def eliminar_notificacion(id_notificacion):
        """
        Elimina una notificación
        
        Args:
            id_notificacion: ID de la notificación
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            result = Notificacion.delete(id_notificacion)
            
            return {
                "success": result.deleted_count > 0,
                "mensaje": "Notificación eliminada"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class NotificacionSistemaHandler:
    """
    Handler especializado para notificaciones del sistema según rol
    """

    # Tipos de notificaciones por rol
    TIPOS_ADMIN = {
        "LOGIN": "🔐 Inicio de Sesión",
        "LOGOUT": "🚪 Cierre de Sesión",
        "ERROR_SISTEMA": "⚠️ Error del Sistema",
        "BACKUP_CREADO": "💾 Backup Creado",
        "BACKUP_RESTAURADO": "🔄 Backup Restaurado",
        "EMPLEADO_CREADO": "👤 Nuevo Empleado",
        "EMPLEADO_ELIMINADO": "❌ Empleado Eliminado",
        "ALERTA_INVENTARIO": "📦 Alerta de Inventario"
    }

    TIPOS_MESERO = {
        "LOGIN": "🔐 Inicio de Sesión",
        "LOGOUT": "🚪 Cierre de Sesión",
        "PEDIDO_ASIGNADO": "📋 Nuevo Pedido",
        "PEDIDO_LISTO": "✅ Pedido Listo",
        "MESA_ASIGNADA": "🍽️ Mesa Asignada",
        "PROPINA_RECIBIDA": "💰 Propina Recibida"
    }

    TIPOS_COCINA = {
        "LOGIN": "🔐 Inicio de Sesión",
        "LOGOUT": "🚪 Cierre de Sesión",
        "PEDIDO_NUEVO": "🔔 Nuevo Pedido",
        "PEDIDO_URGENTE": "⚡ Pedido Urgente",
        "INGREDIENTE_FALTANTE": "⚠️ Ingrediente Faltante"
    }

    TIPOS_INVENTARIO = {
        "LOGIN": "🔐 Inicio de Sesión",
        "LOGOUT": "🚪 Cierre de Sesión",
        "STOCK_BAJO": "📉 Stock Bajo",
        "ENTRADA_REGISTRADA": "📥 Entrada Registrada",
        "SALIDA_REGISTRADA": "📤 Salida Registrada",
        "MERMA_REGISTRADA": "🗑️ Merma Registrada"
    }

    @classmethod
    def notificar_login(cls, id_usuario, nombre_usuario, rol):
        """Notifica inicio de sesión según el rol"""
        mensaje = f"{nombre_usuario} ha iniciado sesión"
        
        return NotificacionCommandHandler.crear_notificacion(
            tipo="LOGIN",
            mensaje=mensaje,
            id_usuario=id_usuario,
            datos_extra={
                "rol": rol,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    @classmethod
    def notificar_logout(cls, id_usuario, nombre_usuario, rol):
        """Notifica cierre de sesión según el rol"""
        mensaje = f"{nombre_usuario} ha cerrado sesión"
        
        return NotificacionCommandHandler.crear_notificacion(
            tipo="LOGOUT",
            mensaje=mensaje,
            id_usuario=id_usuario,
            datos_extra={
                "rol": rol,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    @classmethod
    def notificar_error(cls, id_usuario, tipo_error, descripcion):
        """Notifica un error del sistema"""
        mensaje = f"Error: {descripcion}"
        
        return NotificacionCommandHandler.crear_notificacion(
            tipo="ERROR_SISTEMA",
            mensaje=mensaje,
            id_usuario=id_usuario,
            datos_extra={
                "tipo_error": tipo_error,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    @classmethod
    def notificar_backup(cls, id_usuario, tipo_backup, nombre_archivo):
        """Notifica operaciones de backup"""
        tipo = "BACKUP_CREADO" if tipo_backup == "crear" else "BACKUP_RESTAURADO"
        mensaje = f"Backup {tipo_backup}: {nombre_archivo}"
        
        return NotificacionCommandHandler.crear_notificacion(
            tipo=tipo,
            mensaje=mensaje,
            id_usuario=id_usuario,
            datos_extra={
                "archivo": nombre_archivo,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    @classmethod
    def notificar_empleado(cls, id_admin, accion, nombre_empleado):
        """Notifica acciones sobre empleados (solo admin)"""
        tipo = "EMPLEADO_CREADO" if accion == "crear" else "EMPLEADO_ELIMINADO"
        mensaje = f"Empleado {accion}: {nombre_empleado}"
        
        return NotificacionCommandHandler.crear_notificacion(
            tipo=tipo,
            mensaje=mensaje,
            id_usuario=id_admin,
            datos_extra={
                "empleado": nombre_empleado,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    @classmethod
    def notificar_inventario(cls, id_usuario, tipo_movimiento, nombre_insumo, cantidad):
        """Notifica movimientos de inventario"""
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
                "timestamp": datetime.utcnow().isoformat()
            }
        )