from config.db import db

class GetReportQueries:
    @staticmethod
    def get_sales_summary() -> list:
        """
        Genera un resumen de ventas agrupado por status (estado).
        Retorna una lista de diccionarios con '_id' (status) y 'total' (sum).
        """
        # Verifica si la colección existe antes de intentar la agregación
        if "ventas" in db.list_collection_names():
            pipeline = [
                {"$group": {"_id": "$status", "total": {"$sum": "$amount"}}}
            ]
            return list(db["ventas"].aggregate(pipeline))
        return []

    @staticmethod
    def get_credit_stats(asesor_id: str) -> dict:
        """
        Obtiene estadísticas de créditos (cartera) del asesor.
        """
        stats = {
            # Contamos todos los créditos asignados
            "total_creditos": db["creditos"].count_documents({"asesor_id": asesor_id}),
            
            # Contamos créditos en estado 'mora'
            "morosos": db["creditos"].count_documents({"asesor_id": asesor_id, "estado": "mora"}),
            
            # Contamos créditos en estado 'activo'
            "activos": db["creditos"].count_documents({"asesor_id": asesor_id, "estado": "activo"})
        }
        return stats