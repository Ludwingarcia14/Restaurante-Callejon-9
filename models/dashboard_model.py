from config.db import db

class DashboardModel:

    # Colecciones principales del restaurante
    clientes = db.clientes
    platillos = db.platillos
    pedidos = db.pedidos
    mesas = db.mesas
    usuarios = db.usuarios

    # ============================
    # MÉTRICAS
    # ============================

    @staticmethod
    def count_clientes():
        """Total de clientes registrados."""
        return DashboardModel.clientes.count_documents({})

    @staticmethod
    def count_usuarios():
        """Total de usuarios/empleados internos."""
        return DashboardModel.usuarios.count_documents({})

    @staticmethod
    def count_pedidos():
        """Total de pedidos generados."""
        return DashboardModel.pedidos.count_documents({})

    @staticmethod
    def count_platillos():
        """Total de platillos en el menú."""
        return DashboardModel.platillos.count_documents({})

    @staticmethod
    def count_mesas():
        """Total de mesas registradas."""
        return DashboardModel.mesas.count_documents({})

    # ============================
    # LISTADOS PARA DASHBOARD
    # ============================

    @staticmethod
    def ultimos_clientes(limit=5):
        """Últimos clientes registrados."""
        return list(
            DashboardModel.clientes
            .find({}, {"nombre": 1, "apellidos": 1, "email": 1, "fecha_registro": 1})
            .sort("_id", -1)
            .limit(limit)
        )

    @staticmethod
    def ultimos_pedidos(limit=5):
        """Últimos pedidos realizados."""
        return list(
            DashboardModel.pedidos
            .find({}, {"cliente": 1, "total": 1, "fecha": 1})
            .sort("_id", -1)
            .limit(limit)
        )

    @staticmethod
    def ultimos_platillos(limit=5):
        """Últimos platillos añadidos al menú."""
        return list(
            DashboardModel.platillos
            .find({}, {"nombre": 1, "precio": 1, "categoria": 1})
            .sort("_id", -1)
            .limit(limit)
        )

    # ============================
    # MÉTRICAS FINANCIERAS BÁSICAS
    # ============================

    @staticmethod
    def total_ventas():
        """Suma total de ventas."""
        pipeline = [
            {"$group": {"_id": None, "total": {"$sum": "$total"}}}
        ]
        result = list(DashboardModel.pedidos.aggregate(pipeline))
        return result[0]["total"] if result else 0

    @staticmethod
    def ventas_por_dia():
        """Ventas agrupadas por día."""
        pipeline = [
            {
                "$group": {
                    "_id": "$fecha",
                    "total": {"$sum": "$total"},
                    "pedidos": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        return list(DashboardModel.pedidos.aggregate(pipeline))
