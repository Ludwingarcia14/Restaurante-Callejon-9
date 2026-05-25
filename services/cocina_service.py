from config.db import db
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np


class CocinaService:

    @staticmethod
    def get_pedidos_pendientes() -> list:
        cursor = db.comandas.find({
            "$or": [
                {"estado": "enviada"},
                {"items.estado_cocina": "pendiente"}
            ]
        }).sort("fecha_apertura", 1)

        pedidos = []
        for comanda in cursor:
            items_pendientes = [
                item for item in comanda.get("items", [])
                if item.get("estado_cocina", "pendiente") == "pendiente"
            ]
            if items_pendientes:
                fechas = [i.get("fecha_pedido") for i in items_pendientes if i.get("fecha_pedido")]
                fecha_ref = min(fechas) if fechas else comanda.get("fecha_apertura")
                pedidos.append({
                    "id": str(comanda["_id"]),
                    "folio": comanda.get("folio"),
                    "mesa": comanda.get("mesa_numero"),
                    "mesero": comanda.get("mesero_nombre", "Mesero"),
                    "items": items_pendientes,
                    "num_items": len(items_pendientes),
                    "fecha_pedido": fecha_ref,
                    "tiempo_espera": calcular_tiempo_espera(fecha_ref)
                })
        return pedidos

    @staticmethod
    def get_pedidos_en_proceso() -> list:
        cursor = db.comandas.find({"items.estado_cocina": "en_preparacion"}).sort("fecha_apertura", 1)
        pedidos = []
        for comanda in cursor:
            items_en_proceso = [
                item for item in comanda.get("items", [])
                if item.get("estado_cocina") == "en_preparacion"
            ]
            if items_en_proceso:
                pedidos.append({
                    "id": str(comanda["_id"]),
                    "folio": comanda.get("folio"),
                    "mesa": comanda.get("mesa_numero"),
                    "items": items_en_proceso,
                    "fecha_inicio": items_en_proceso[0].get("fecha_inicio_preparacion"),
                    "tiempo_preparacion": calcular_tiempo_espera(
                        items_en_proceso[0].get("fecha_inicio_preparacion")
                    )
                })
        return pedidos

    @staticmethod
    def get_pedidos_listos() -> list:
        cursor = db.comandas.find({"items.estado_cocina": "listo"}).sort("fecha_apertura", -1)
        pedidos = []
        for comanda in cursor:
            items_listos = [
                item for item in comanda.get("items", [])
                if item.get("estado_cocina") == "listo"
            ]
            if items_listos:
                pedidos.append({
                    "id": str(comanda["_id"]),
                    "folio": comanda.get("folio"),
                    "mesa": comanda.get("mesa_numero"),
                    "items": items_listos,
                    "fecha_listo": items_listos[0].get("fecha_listo")
                })
        return pedidos

    @staticmethod
    def iniciar_preparacion(comanda_id: str, item_ids: list, cocinero_id: str) -> bool:
        result = db.comandas.update_one(
            {"_id": ObjectId(comanda_id)},
            {"$set": {
                "items.$[item].estado_cocina": "en_preparacion",
                "items.$[item].fecha_inicio_preparacion": datetime.utcnow(),
                "items.$[item].cocinero_id": ObjectId(cocinero_id)
            }},
            array_filters=[{"item.producto_id": {"$in": item_ids}}]
        )
        if result.modified_count > 0:
            _emitir_evento_cocina(comanda_id, "preparacion_iniciada", item_ids)
            return True
        return False

    @staticmethod
    def marcar_listo(comanda_id: str, item_ids: list) -> bool:
        result = db.comandas.update_one(
            {"_id": ObjectId(comanda_id)},
            {"$set": {
                "items.$[item].estado_cocina": "listo",
                "items.$[item].fecha_listo": datetime.utcnow()
            }},
            array_filters=[{"item.producto_id": {"$in": item_ids}}]
        )
        if result.modified_count > 0:
            comanda = db.comandas.find_one({"_id": ObjectId(comanda_id)})
            _notificar_mesero_listo(
                str(comanda.get("mesero_id")),
                comanda_id,
                comanda.get("mesa_numero"),
                item_ids
            )
            return True
        return False

    @staticmethod
    def marcar_entregado(comanda_id: str, item_ids: list) -> bool:
        result = db.comandas.update_one(
            {"_id": ObjectId(comanda_id)},
            {"$set": {
                "items.$[item].estado_cocina": "entregado",
                "items.$[item].fecha_entregado": datetime.utcnow()
            }},
            array_filters=[{"item.producto_id": {"$in": item_ids}}]
        )
        return result.modified_count > 0

    @staticmethod
    def get_estadisticas() -> dict:
        hoy_inicio = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        pipeline = [
            {"$match": {"fecha_apertura": {"$gte": hoy_inicio, "$lt": hoy_inicio + timedelta(days=1)}}},
            {"$unwind": "$items"},
            {"$group": {"_id": "$items.estado_cocina", "count": {"$sum": 1}}}
        ]
        stats = {"pendientes": 0, "en_preparacion": 0, "listos": 0, "entregados": 0, "total_procesados": 0}
        for r in db.comandas.aggregate(pipeline):
            estado = r.get("_id", "pendiente")
            count = r.get("count", 0)
            if estado in stats:
                stats[estado] = count
            stats["total_procesados"] += count
        return stats

    @staticmethod
    def get_top_platillos(dias: int = 30) -> list:
        fecha_inicio = datetime.utcnow() - timedelta(days=dias)
        pipeline = [
            {"$match": {
                "fecha_apertura": {"$gte": fecha_inicio},
                "estado": {"$in": ["pagada", "cerrada", "lista", "enviada"]}
            }},
            {"$unwind": "$items"},
            {"$match": {"items.nombre": {"$exists": True, "$ne": None}}},
            {"$group": {
                "_id": "$items.nombre",
                "total_unidades": {"$sum": "$items.cantidad"},
                "num_comandas": {"$sum": 1}
            }},
            {"$sort": {"total_unidades": -1}},
            {"$limit": 10},
            {"$project": {"platillo": "$_id", "total_unidades": 1, "num_comandas": 1, "_id": 0}}
        ]
        return list(db.comandas.aggregate(pipeline))

    @staticmethod
    def get_kmeans_platillos(dias: int = 30) -> dict:
        fecha_inicio = datetime.utcnow() - timedelta(days=dias)
        pipeline = [
            {"$match": {
                "fecha_apertura": {"$gte": fecha_inicio},
                "estado": {"$in": ["pagada", "cerrada", "lista", "enviada"]}
            }},
            {"$unwind": "$items"},
            {"$match": {"items.nombre": {"$exists": True, "$ne": None}}},
            {"$group": {
                "_id": "$items.nombre",
                "total_unidades": {"$sum": "$items.cantidad"},
                "num_comandas": {"$sum": 1}
            }},
            {"$match": {"total_unidades": {"$gte": 1}}}
        ]
        datos = list(db.comandas.aggregate(pipeline))

        if len(datos) < 3:
            return {
                "puntos": [],
                "aviso": "Se necesitan al menos 3 platillos con pedidos para ejecutar K-Means."
            }

        nombres = [d["_id"] for d in datos]
        X_raw = np.array([[float(d["total_unidades"]), float(d["num_comandas"])] for d in datos])

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_raw)

        k = min(3, len(datos))
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)

        centroids_orig = scaler.inverse_transform(km.cluster_centers_)
        orden = np.argsort(centroids_orig[:, 0] + centroids_orig[:, 1])[::-1]
        remap = {old: new for new, old in enumerate(orden)}
        labels_remap = [remap[l] for l in km.labels_]

        meta = [
            {"label": "Estrellas",   "color": "#f59e0b", "bg": "#fef3c7"},
            {"label": "Frecuentes",  "color": "#3b82f6", "bg": "#dbeafe"},
            {"label": "Ocasionales", "color": "#94a3b8", "bg": "#f1f5f9"},
        ]

        puntos = []
        for i, d in enumerate(datos):
            cl = int(labels_remap[i])
            m = meta[cl] if cl < len(meta) else meta[-1]
            puntos.append({
                "platillo": nombres[i],
                "x": round(float(d["total_unidades"]), 1),
                "y": round(float(d["num_comandas"]), 1),
                "cluster": cl,
                "label": m["label"],
                "color": m["color"],
                "bg": m["bg"],
            })

        return {"puntos": puntos, "periodo_dias": dias}


# ── Utilidades de tiempo y socket (privadas al módulo) ──────────────────────

def calcular_tiempo_espera(fecha_inicio) -> int:
    if not fecha_inicio:
        return 0
    return int((datetime.utcnow() - fecha_inicio).total_seconds() / 60)


def _emitir_evento_cocina(comanda_id, evento, data):
    try:
        from extensions import socketio
        socketio.emit(
            evento,
            {"comanda_id": comanda_id, "data": data, "timestamp": datetime.utcnow().isoformat()},
            room="cocina",
            namespace="/"
        )
    except Exception as e:
        print(f"⚠️ Error Socket.IO cocina: {e}")


def _notificar_mesero_listo(mesero_id, comanda_id, mesa_numero, item_ids):
    try:
        from extensions import socketio
        from cqrs.commands.handlers.notificacion_handler import NotificacionSistemaHandler
        NotificacionSistemaHandler.notificar_pedido_listo(
            mesero_id=mesero_id,
            comanda_id=comanda_id,
            mesa_numero=mesa_numero
        )
        socketio.emit(
            "pedido_listo",
            {"comanda_id": comanda_id, "mesa": mesa_numero, "items": item_ids},
            room=f"user_{mesero_id}",
            namespace="/"
        )
    except Exception as e:
        print(f"⚠️ Error al notificar mesero: {e}")
