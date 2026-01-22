from config.db import db
from datetime import datetime
from typing import Dict, Any
from flask import current_app

class UpdateConfigGeneralCommand:
    def __init__(self, data: Dict[str, Any], financiera_id: str, session_data: Dict[str, Any]):
        self.data = data
        self.financiera_id = financiera_id
        self.session_data = session_data

    def execute(self) -> Dict[str, Any]:
        """
        Actualiza la configuración general de la financiera en la colección 'configuracion'
        y registra la acción en la colección 'auditoria'.
        """
        # 1. Mapear y convertir datos (para asegurar tipos correctos)
        try:
            config_actualizada = {
                "tasa_interes_anual": float(self.data.get("tasa_interes_anual", 18.0)),
                "tasa_mora_mensual": float(self.data.get("tasa_mora_mensual", 5.0)),
                "plazo_minimo_meses": int(self.data.get("plazo_minimo_meses", 6)),
                "plazo_maximo_meses": int(self.data.get("plazo_maximo_meses", 60)),
                "monto_minimo": float(self.data.get("monto_minimo", 5000.0)),
                "monto_maximo": float(self.data.get("monto_maximo", 500000.0)),
                "dia_corte_mensual": int(self.data.get("dia_corte_mensual", 15)),
                "dias_gracia": int(self.data.get("dias_gracia", 5)),
                "comision_apertura_porcentaje": float(self.data.get("comision_apertura_porcentaje", 2.0)),
                "iva_porcentaje": float(self.data.get("iva_porcentaje", 16.0)),
                "score_minimo_aprobacion": int(self.data.get("score_minimo_aprobacion", 650)),
                # Convertir strings "true"/"false" a booleanos
                "permite_renovacion": str(self.data.get("permite_renovacion")).lower() == "true",
                "permite_pago_anticipado": str(self.data.get("permite_pago_anticipado")).lower() == "true",
                "penalizacion_pago_anticipado": float(self.data.get("penalizacion_pago_anticipado", 0.0)),
                "email_notificaciones": str(self.data.get("email_notificaciones", "")).strip(),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            current_app.logger.error(f"Error de conversión en config: {e}")
            raise ValueError(f"Datos de configuración inválidos: {str(e)}")

        # 2. Ejecutar la actualización con upsert=True (si no existe, lo crea)
        result = db.configuracion.update_one(
            {"financiera_id": self.financiera_id},
            {"$set": config_actualizada},
            upsert=True
        )

        # 3. Registrar en auditoría si hubo cambio
        if result.matched_count > 0 or result.upserted_id:
            db.auditoria.insert_one({
                "usuario_id": self.session_data.get("usuario_id"),
                "usuario_nombre": self.session_data.get("usuario_nombre"),
                "accion": "Actualización de configuración general",
                "modulo": "configuracion",
                "detalles": config_actualizada,
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            return {"success": True, "matched_count": result.matched_count, "upserted_id": str(result.upserted_id)}
        else:
            return {"success": False, "matched_count": result.matched_count, "upserted_id": None}