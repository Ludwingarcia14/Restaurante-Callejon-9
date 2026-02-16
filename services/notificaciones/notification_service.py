"""
Servicio de Notificaciones - Restaurante Callejón 9
Versión simplificada con modo local para desarrollo
"""

import os
import logging
from datetime import datetime
from pytz import timezone

# Configuración
USE_LOCAL = os.getenv("USE_LOCAL_SOCKET", "true").lower() == "true"
NODE_NOTIFICATIONS_URL = os.getenv("NODE_NOTIFICATIONS_URL", "http://localhost:8000")

# Zona horaria de Mexico City (CST/CDT)
Mexico_TZ = timezone('America/Mexico_City')

def get_mexico_datetime():
    """Obtiene la fecha y hora actual en zona horaria de Mexico"""
    return datetime.now(Mexico_TZ)


def notificar_usuario(user_id, evento, mensaje, datos_extra=None):
    """
    Envía una notificación push en tiempo real
    
    Modos:
    - LOCAL: Solo registra en logs (desarrollo)
    - REMOTE: Envía a servidor externo (producción)
    
    Args:
        user_id: ID del usuario destinatario
        evento: Tipo de evento (LOGIN, LOGOUT, ERROR, etc.)
        mensaje: Mensaje descriptivo
        datos_extra: Datos adicionales opcionales
        
    Returns:
        dict: Resultado de la operación
    """
    
    # MODO LOCAL (Desarrollo)
    if USE_LOCAL:
        logging.info(f"[NOTIF LOCAL] 📬 {evento} para user {user_id}: {mensaje}")
        
        # Simular éxito
        return {
            "success": True, 
            "mode": "local",
            "mensaje": "Notificación registrada localmente"
        }
    
    # MODO REMOTO (Producción con servidor Socket.IO)
    try:
        import requests
        
        payload = {
            "user_id": str(user_id),
            "evento": evento,
            "mensaje": mensaje,
            "datos_extra": datos_extra or {},
            "timestamp": get_mexico_datetime().isoformat()
        }
        
        # Timeout de 30 segundos (suficiente para despertar servidor en Render)
        response = requests.post(
            f"{NODE_NOTIFICATIONS_URL}/api/notify",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            logging.info(f"✅ Notificación enviada: {evento} -> user {user_id}")
            return {
                "success": True, 
                "mode": "remote",
                "mensaje": "Notificación enviada al servidor"
            }
        else:
            logging.warning(f"⚠️ Error al enviar notificación: {response.status_code}")
            return {
                "success": False, 
                "error": response.text,
                "mode": "remote_error"
            }
            
    except Exception as e:
        logging.error(f"❌ Error de conexión: {e}")
        
        # Fallback: registrar en logs
        logging.info(f"[FALLBACK] {evento} para user {user_id}: {mensaje}")
        
        return {
            "success": False, 
            "error": str(e), 
            "mode": "fallback"
        }


def enviar_notificacion_masiva(user_ids, evento, mensaje, datos_extra=None):
    """
    Envía una notificación a múltiples usuarios
    
    Args:
        user_ids: Lista de IDs de usuarios
        evento: Tipo de evento
        mensaje: Mensaje
        datos_extra: Datos adicionales
        
    Returns:
        dict: Resumen de envíos
    """
    resultados = {
        "exitosos": 0,
        "fallidos": 0,
        "total": len(user_ids)
    }
    
    for user_id in user_ids:
        resultado = notificar_usuario(user_id, evento, mensaje, datos_extra)
        
        if resultado.get("success"):
            resultados["exitosos"] += 1
        else:
            resultados["fallidos"] += 1
    
    logging.info(
        f"[MASIVO] {resultados['exitosos']}/{resultados['total']} "
        f"notificaciones enviadas para evento {evento}"
    )
    
    return resultados