from config.db import db
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np


class CocinaService:

    @staticmethod
    def get_pedidos_movil_pendientes() -> list:
        """
        Pedidos hechos por clientes desde la app/wearable (colección pedidos_movil),
        pendientes de preparar. Reutiliza el mismo modelo que usa la API /api/v1,
        pero se consulta aquí vía sesión (empleado), no JWT.
        """
        from models.pedido_movil_model import PedidoMovil
        pedidos = PedidoMovil.find_pendientes_cocina()
        return [PedidoMovil.to_public(p) for p in pedidos]

    @staticmethod
    def actualizar_estado_pedido_movil(pedido_id: str, nuevo_estado: str) -> bool:
        from models.pedido_movil_model import PedidoMovil, ESTADOS_VALIDOS
        if nuevo_estado not in ESTADOS_VALIDOS:
            return False
        doc = PedidoMovil.find_by_id(pedido_id)
        if not doc:
            return False
        PedidoMovil.update_estado(pedido_id, nuevo_estado)
        doc["estado"] = nuevo_estado
        _emitir_actualizacion_cliente_movil(doc.get("cliente_id", ""), doc)
        _emitir_pedido_movil_a_cocina(pedido_id, nuevo_estado)

        # ── NUEVO FLUJO: la orden de entrega nace cuando Cocina marca 'listo' ──
        # Antes el DeliveryOrder se creaba al momento del pedido (ver
        # controllers/api/v1/pedido_movil_controller.py::crear_pedido, hoy
        # desactivado). Ahora se crea aquí, ya 'listo para recoger', y se
        # notifica a todos los repartidores conectados para que uno lo acepte.
        # La condición delivery_order_id=None respeta pedidos antiguos que ya
        # traían una orden creada por el flujo anterior.
        if (
            nuevo_estado == "listo"
            and doc.get("tipo_entrega") == "delivery"
            and not doc.get("delivery_order_id")
        ):
            delivery_id = _crear_delivery_al_marcar_listo(pedido_id, doc)
            if delivery_id:
                doc["delivery_order_id"] = delivery_id

        # ── Propagar el avance de cocina a la orden de entrega (si existe) ──
        # Este era el eslabon faltante: antes, el DeliveryOrder nunca se enteraba
        # de que Cocina habia terminado, y el Administrador no tenia forma de saber
        # que pedidos ya estaban listos para asignar repartidor.
        if doc.get("delivery_order_id"):
            _sincronizar_delivery_con_cocina(pedido_id, nuevo_estado, doc)

        return True

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

def _emitir_pedido_movil_a_cocina(pedido_id: str, nuevo_estado: str):
    """
    Avisa a la sala 'cocina' que un pedido móvil cambió de estado, para que la
    vista de pedidos reubique la tarjeta (en proceso ↔ completados) en tiempo
    real en todas las pantallas de cocina abiertas.
    """
    try:
        from extensions import socketio
        socketio.emit(
            "pedido_movil_actualizado",
            {"pedido_id": str(pedido_id), "estado": nuevo_estado},
            room="cocina",
            namespace="/",
        )
    except Exception as e:
        print(f"⚠️ Error Socket.IO pedido_movil_actualizado: {e}")

def _crear_delivery_al_marcar_listo(pedido_id: str, pedido_doc: dict):
    """
    Crea la orden de entrega en el momento en que Cocina marca 'listo' un pedido
    móvil a domicilio, la enlaza al PedidoMovil y avisa a la sala
    'repartidores_global' (a la que todo repartidor se une al conectar, ver
    app.py::on join_repartidor) para que cualquiera pueda aceptarla.

    Devuelve el ObjectId (str) del DeliveryOrder creado, o None si falló.
    """
    from pymongo.errors import DuplicateKeyError

    try:
        from models.delivery_model import DeliveryOrder
        from models.pedido_movil_model import PedidoMovil
        from models.cliente_model import Cliente

        cliente_doc = Cliente.find_by_id(pedido_doc.get("cliente_id", ""))
        ubicacion = pedido_doc.get("ubicacion") or {}

        delivery_id = DeliveryOrder.crear({
            "tipo": "pedido_movil",
            "pedido_movil_id": pedido_id,
            "cliente_id": pedido_doc.get("cliente_id"),
            "cliente_nombre": f"{cliente_doc.get('nombre','')} {cliente_doc.get('apellidos','')}".strip() if cliente_doc else "",
            "cliente_telefono": cliente_doc.get("telefono", "") if cliente_doc else "",
            "direccion": pedido_doc.get("direccion", ""),
            "referencias": pedido_doc.get("referencias", ""),
            "cliente_lat": ubicacion.get("lat"),
            "cliente_lng": ubicacion.get("lng"),
            "cliente_ubicacion_accuracy": ubicacion.get("accuracy"),
            "items": pedido_doc.get("items", []),
            "total": pedido_doc.get("total", 0),
            "notas": pedido_doc.get("notas", ""),
            "tenant_id": pedido_doc.get("tenant_id", ""),
            # Nace listo: cocina acaba de terminarlo.
            "estado_cocina": "listo",
        })
        PedidoMovil.set_delivery_order_id(pedido_id, delivery_id)
    except DuplicateKeyError:
        # Carrera: otra petición 'listo' simultánea ya insertó la orden (índice
        # único uniq_pedido_movil_id, ver DeliveryOrder.ensure_indexes). Se
        # recupera la existente y se repara el enlace por si el ganador no
        # alcanzó a escribirlo; NO se re-emite la notificación a repartidores
        # (la emitió, o la está emitiendo, la petición ganadora).
        try:
            existente = DeliveryOrder.get_by_pedido_movil(pedido_id)
            if existente:
                delivery_id = str(existente["_id"])
                PedidoMovil.set_delivery_order_id(pedido_id, delivery_id)
                return delivery_id
        except Exception as e:
            print(f"⚠️ No se pudo recuperar la orden de entrega existente: {e}")
        return None
    except Exception as e:
        print(f"⚠️ No se pudo crear la orden de entrega al marcar listo: {e}")
        return None

    try:
        from extensions import socketio
        delivery = DeliveryOrder.get_by_id(delivery_id)
        socketio.emit(
            "nuevo_pedido_disponible",
            {
                "delivery_id": str(delivery_id),
                "folio": delivery.get("folio", "") if delivery else "",
                "pedido_folio": pedido_doc.get("folio", ""),
                "cliente_nombre": delivery.get("cliente_nombre", "") if delivery else "",
                "direccion": pedido_doc.get("direccion", ""),
                "referencias": pedido_doc.get("referencias", ""),
                "total": pedido_doc.get("total", 0),
                "tiempo_estimado": delivery.get("tiempo_estimado", 30) if delivery else 30,
            },
            room="repartidores_global",
            namespace="/",
        )
    except Exception as e:
        print(f"⚠️ Error Socket.IO hacia repartidores_global: {e}")

    return delivery_id


def _sincronizar_delivery_con_cocina(pedido_id: str, estado_cocina: str, pedido_doc: dict):
    """
    Refleja el avance de Cocina en la orden de entrega ya existente y avisa al
    panel del Administrador para que la lista se refresque sin recargar.

    NO crea ningun DeliveryOrder nuevo (la relacion PedidoMovil <-> DeliveryOrder
    es 1:1 y el documento se creo al momento del pedido, ver
    controllers/api/v1/pedido_movil_controller.py::crear_pedido).
    NO modifica DeliveryOrder.estado, que pertenece al flujo Admin/Repartidor.
    """
    try:
        from models.delivery_model import DeliveryOrder
        DeliveryOrder.set_estado_cocina(pedido_id, estado_cocina)
    except Exception as e:
        print(f"⚠️ No se pudo sincronizar el estado de cocina con delivery: {e}")
        return

    try:
        from extensions import socketio
        socketio.emit(
            "delivery_cocina_actualizado",
            {
                "pedido_movil_id": str(pedido_id),
                "delivery_order_id": str(pedido_doc.get("delivery_order_id")),
                "estado_cocina": estado_cocina,
                "folio": pedido_doc.get("folio", ""),
                "listo_para_asignar": estado_cocina == "listo",
            },
            room="admins",
            namespace="/",
        )
    except Exception as e:
        print(f"⚠️ Error Socket.IO hacia admins: {e}")


def _emitir_actualizacion_cliente_movil(cliente_id: str, pedido_doc: dict):
    """
    Notifica al cliente (sala 'cliente_{id}') el nuevo estado de su pedido movil,
    desde el flujo de Cocina (sesion). Misma sala/evento que usa
    controllers/api/v1/pedido_movil_controller.py para mantener consistencia.
    """
    if not cliente_id:
        return
    try:
        from extensions import socketio
        socketio.emit(
            "pedido_actualizado",
            {
                "pedido_id": str(pedido_doc["_id"]),
                "estado": pedido_doc.get("estado"),
                "folio": pedido_doc.get("folio"),
            },
            room=f"cliente_{cliente_id}",
            namespace="/",
        )
    except Exception as e:
        print(f"⚠️ Error Socket.IO cliente movil: {e}")


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
