from config.db import db
from bson.objectid import ObjectId

class GetDashboardQueries:
    # Solución Reforzada: Priorizar la solicitud que tenga el Buró de Crédito.

    @staticmethod
    def get_active_solicitud(cliente_id: str, tipo_persona: str) -> dict:

        if tipo_persona.lower() == "fisica":
            coleccion = db.documentofisica
            campo_buro_analisis = "documentos.buro_credito_fisica.analisis_buro"
        elif tipo_persona.lower() == "moral":
            coleccion = db.documentomoral
            campo_buro_analisis = "documentos.buro_credito_moral.analisis_buro"
        else:
            print(f"Tipo de persona no reconocido: {tipo_persona}")
            return None

        try:
            user_id = ObjectId(cliente_id)
        except Exception as e:
            print(f"ObjectId inválido: {cliente_id} → {e}")
            return None

        query_final = {
            "usuario_id": user_id,
            "tipo_persona": tipo_persona.lower(),
            campo_buro_analisis: {"$exists": True}
        }

        solicitud = coleccion.find_one(
            query_final,
            sort=[("created_at", -1)]
        )

        if not solicitud:
            print("❌ No se encontró solicitud")
            print("Query:", query_final)
        else:
            print("✅ Solicitud encontrada")

        return solicitud

    @staticmethod
    def get_asesor_info(asesor_id_str: str) -> dict:
        """Busca el documento de usuario del asesor."""
        try:
            return db.usuarios.find_one({"_id": ObjectId(asesor_id_str)})
        except Exception:
            return None

    @staticmethod
    def get_historial_creditos(cliente_id: str) -> list:
        """Obtiene todo el historial de solicitudes de crédito del cliente."""
        return list(db.solicitudes.find({"user_id": cliente_id}).sort("fecha", -1))