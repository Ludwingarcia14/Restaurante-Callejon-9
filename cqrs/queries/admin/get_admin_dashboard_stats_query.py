"""
Query para obtener las estadísticas del Dashboard del Administrador.
"""
from config.db import db

class GetAdminDashboardStatsQuery:
    """
    Recupera el conteo de documentos para diferentes roles y colecciones.
    """
    @staticmethod
    def execute():
        """
        Ejecuta la consulta de conteo en MongoDB.

        Returns:
            dict: Un diccionario con las estadísticas del dashboard.
        """
        try:
            stats = {
                # Cuentas de usuarios administrativos/plataforma
                "super_administradores": db.usuarios.count_documents({"usuario_rol": "1"}),
                "administrador": db.usuarios.count_documents({"usuario_rol": "2"}),
                "financiera": db.usuarios.count_documents({"usuario_rol": "5"}),
                "usuarios_plataforma_total": db.usuarios.count_documents({}),
                
                # Cuentas de clientes (colección separada)
                "clientes": db.clientes.count_documents({}),
            }
            return stats, None # Retorna los datos y ningún error
        except Exception as e:
            return None, str(e) # Retorna None y el error