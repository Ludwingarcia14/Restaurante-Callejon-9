from config.db import db
from bson.objectid import ObjectId
from typing import Optional

class GetSolicitudQueries:
    @staticmethod
    def get_solicitudes_with_asesor(cliente_id_obj: ObjectId) -> list:
        """
        Obtiene todas las solicitudes de crédito del cliente, incluyendo la información del asesor
        (Simula el join realizado en el controlador original)
        """
        solicitudes = list(db.credito.find({"cliente_id": cliente_id_obj}))

        for s in solicitudes:
            asesor_id = s.get("asesor")
            if asesor_id:
                try:
                    asesor = db.asesores.find_one({"_id": ObjectId(asesor_id)})
                    s["nombre_asesor"] = asesor.get("nombre", "-") if asesor else "-"
                    s["telefono_asesor"] = asesor.get("telefono", "-") if asesor else "-"
                    s["correo_asesor"] = asesor.get("correo", "-") if asesor else "-"
                except Exception:
                    s["nombre_asesor"] = "-"
                    s["telefono_asesor"] = "-"
                    s["correo_asesor"] = "-"
            else:
                s["nombre_asesor"] = "-"
                s["telefono_asesor"] = "-"
                s["correo_asesor"] = "-"
        return solicitudes

    @staticmethod
    def get_solicitud_by_id(solicitud_id: str) -> Optional[dict]:
        """Obtiene una solicitud de crédito por su _id."""
        try:
            return db.credito.find_one({"_id": ObjectId(solicitud_id)})
        except Exception:
            return None

    @staticmethod
    def get_asesor_for_solicitud(asesor_id: str) -> Optional[dict]:
        """Obtiene la información detallada del asesor asignado."""
        try:
            return db.asesores.find_one({"_id": ObjectId(asesor_id)})
        except Exception:
            return None