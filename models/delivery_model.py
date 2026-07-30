from config.db import db
from datetime import datetime
from bson.objectid import ObjectId
from pymongo import ReturnDocument


class DeliveryOrder:

    @staticmethod
    def _col():
        return db["delivery_orders"]

    @classmethod
    def crear(cls, data):
        doc = {
            "tipo":              data.get("tipo", "directo"),   # 'comanda' | 'directo' | 'pedido_movil'
            "comanda_id":        ObjectId(data["comanda_id"]) if data.get("comanda_id") else None,
            "pedido_movil_id":   ObjectId(data["pedido_movil_id"]) if data.get("pedido_movil_id") else None,
            "cliente_id":        data.get("cliente_id"),  # id del Cliente (colección clientes), si aplica
            "folio":             f"DEL-{datetime.now().strftime('%y%m%d%H%M%S')}",
            "cliente_nombre":    data.get("cliente_nombre", ""),
            "cliente_telefono":  data.get("cliente_telefono", ""),
            "direccion":         data.get("direccion", ""),
            "referencias":       data.get("referencias", ""),
            # Coordenadas reales del cliente (opcional). direccion sigue siendo el fallback
            # para pedidos antiguos o cuando el cliente no otorga permiso de GPS.
            "cliente_lat":                data.get("cliente_lat"),
            "cliente_lng":                data.get("cliente_lng"),
            "cliente_ubicacion_accuracy": data.get("cliente_ubicacion_accuracy"),
            "items":             data.get("items", []),
            "total":             float(data.get("total", 0)),
            "estado":            "pendiente",
            # Avance de COCINA del PedidoMovil asociado (pendiente/en_cocina/listo...).
            # Independiente de 'estado', que es el avance de la ENTREGA.
            "estado_cocina":     data.get("estado_cocina", "pendiente"),
            "repartidor_id":     None,
            "repartidor_nombre": "",
            "creado_por_id":     data.get("creado_por_id"),
            "creado_por_nombre": data.get("creado_por_nombre", ""),
            "tenant_id":         data.get("tenant_id", ""),
            "notas":             data.get("notas", ""),
            "metodo_pago":       data.get("metodo_pago", "efectivo"),
            "pagado":            False,
            "tiempo_estimado":   int(data.get("tiempo_estimado", 30)),
            "created_at":        datetime.utcnow(),
            "updated_at":        datetime.utcnow(),
            "entregado_at":      None,
        }
        res = cls._col().insert_one(doc)
        return str(res.inserted_id)

    @classmethod
    def set_ubicacion_cliente(cls, delivery_id, lat, lng, accuracy=None):
        """Guarda/actualiza las coordenadas GPS reales del cliente para esta entrega."""
        return cls._col().update_one(
            {"_id": ObjectId(delivery_id)},
            {"$set": {
                "cliente_lat": float(lat),
                "cliente_lng": float(lng),
                "cliente_ubicacion_accuracy": float(accuracy) if accuracy is not None else None,
                "updated_at": datetime.utcnow(),
            }}
        )

    @classmethod
    def get_by_id(cls, delivery_id):
        return cls._col().find_one({"_id": ObjectId(delivery_id)})

    @classmethod
    def get_by_pedido_movil(cls, pedido_movil_id):
        """
        Orden de entrega asociada a un PedidoMovil. Gracias al índice único
        uniq_pedido_movil_id (ensure_indexes) hay a lo más un documento.
        """
        return cls._col().find_one({"pedido_movil_id": ObjectId(pedido_movil_id)})

    @classmethod
    def ensure_indexes(cls):
        """
        Garantiza a nivel de BD la relación 1:1 PedidoMovil ↔ DeliveryOrder:
        ante dos creaciones concurrentes (doble clic en 'Marcar listo'), la
        segunda inserción falla con DuplicateKeyError y el servicio de cocina
        recupera la orden ya existente en lugar de duplicarla.

        Índice PARCIAL: solo aplica cuando pedido_movil_id es ObjectId, para no
        chocar con órdenes 'directo'/'comanda' donde el campo es None.
        """
        try:
            cls._col().create_index(
                "pedido_movil_id",
                unique=True,
                partialFilterExpression={"pedido_movil_id": {"$type": "objectId"}},
                name="uniq_pedido_movil_id",
            )
        except Exception as e:
            # Falla típica: ya existen duplicados históricos en delivery_orders.
            # La app arranca igual, pero la garantía 1:1 queda desactivada hasta
            # depurar esos documentos.
            print(f"⚠️ No se pudo crear uniq_pedido_movil_id (¿duplicados previos?): {e}")

    @classmethod
    def get_by_folio(cls, folio):
        return cls._col().find_one({"folio": folio.upper()})

    @classmethod
    def asignar_repartidor(cls, delivery_id, repartidor_id, repartidor_nombre):
        return cls._col().update_one(
            {"_id": ObjectId(delivery_id)},
            {"$set": {
                "repartidor_id":     ObjectId(repartidor_id),
                "repartidor_nombre": repartidor_nombre,
                "estado":            "asignado",
                "updated_at":        datetime.utcnow(),
            }}
        )

    @classmethod
    def aceptar_por_repartidor(cls, delivery_id, repartidor_id, repartidor_nombre):
        """
        Auto-asignación desde el módulo Repartidor (nuevo flujo: el repartidor
        acepta, el Admin solo monitorea). Operación ATÓMICA: el filtro exige
        repartidor_id=None y estado='pendiente', de modo que si dos repartidores
        aceptan el mismo pedido a la vez, solo el primero gana; para el segundo
        no hay documento que coincida y se devuelve None (el controlador
        responde 409).
        """
        return cls._col().find_one_and_update(
            {
                "_id": ObjectId(delivery_id),
                "repartidor_id": None,
                "estado": "pendiente",
            },
            {"$set": {
                "repartidor_id":     ObjectId(repartidor_id),
                "repartidor_nombre": repartidor_nombre,
                "estado":            "asignado",
                "updated_at":        datetime.utcnow(),
            }},
            return_document=ReturnDocument.AFTER,
        )

    @classmethod
    def listar_disponibles(cls, tenant_id=None):
        """
        Pedidos listos en cocina esperando a que un repartidor los acepte.
        En el nuevo flujo el DeliveryOrder se crea cuando Cocina marca 'listo'
        (services/cocina_service.py), por lo que estado='pendiente' +
        repartidor_id=None significa exactamente 'disponible para aceptar'.
        """
        q = {
            "estado": "pendiente",
            "repartidor_id": None,
            "tipo": "pedido_movil",
            # Excluye órdenes residuales del flujo anterior (nacían al momento
            # del pedido, con cocina aún sin terminar). Las del flujo nuevo
            # siempre nacen con estado_cocina='listo'.
            "estado_cocina": "listo",
        }
        if tenant_id:
            q["tenant_id"] = tenant_id
        return list(cls._col().find(q).sort("created_at", 1))

    @classmethod
    def actualizar_estado(cls, delivery_id, nuevo_estado):
        update = {"estado": nuevo_estado, "updated_at": datetime.utcnow()}
        if nuevo_estado == "entregado":
            update["entregado_at"] = datetime.utcnow()
            update["pagado"] = True
        return cls._col().update_one({"_id": ObjectId(delivery_id)}, {"$set": update})

    @classmethod
    def set_estado_cocina(cls, pedido_movil_id, estado_cocina):
        """
        Refleja en la orden de entrega el avance de COCINA del PedidoMovil asociado.

        IMPORTANTE: escribe en el campo 'estado_cocina', NUNCA en 'estado'.
        'estado' es el estado de la ENTREGA (pendiente/asignado/en_camino/entregado)
        y lo controlan el Administrador y el Repartidor; sobrescribirlo aquí sacaría
        el pedido del filtro de listar_pendientes() y rompería el panel y el módulo
        del repartidor.
        """
        return cls._col().update_one(
            {"pedido_movil_id": ObjectId(pedido_movil_id)},
            {"$set": {"estado_cocina": estado_cocina, "updated_at": datetime.utcnow()}},
        )

    @classmethod
    def listar_pendientes(cls, tenant_id=None, tipo=None):
        q = {"estado": {"$in": ["pendiente", "asignado", "en_camino"]}}
        if tenant_id:
            q["tenant_id"] = tenant_id
        if tipo:
            q["tipo"] = tipo
        return list(cls._col().find(q).sort("created_at", 1))

    @classmethod
    def listar_por_repartidor(cls, repartidor_id, solo_activos=True):
        q = {"repartidor_id": ObjectId(repartidor_id)}
        if solo_activos:
            q["estado"] = {"$in": ["asignado", "en_camino"]}
        return list(cls._col().find(q).sort("updated_at", -1))

    @classmethod
    def historial(cls, tenant_id=None, repartidor_id=None, limit=100):
        q = {"estado": {"$in": ["entregado", "cancelado"]}}
        if tenant_id:
            q["tenant_id"] = tenant_id
        if repartidor_id:
            q["repartidor_id"] = ObjectId(repartidor_id)
        return list(cls._col().find(q).sort("updated_at", -1).limit(limit))

    @classmethod
    def stats_repartidor(cls, repartidor_id):
        pipeline = [
            {"$match": {"repartidor_id": ObjectId(repartidor_id), "estado": "entregado"}},
            {"$group": {
                "_id": None,
                "total_entregas": {"$sum": 1},
                "total_ingresos": {"$sum": "$total"},
            }}
        ]
        res = list(cls._col().aggregate(pipeline))
        return res[0] if res else {"total_entregas": 0, "total_ingresos": 0}

    @classmethod
    def stats_globales(cls, tenant_id=None):
        q = {}
        if tenant_id:
            q["tenant_id"] = tenant_id
        pipeline = [
            {"$match": q},
            {"$group": {
                "_id": "$estado",
                "count": {"$sum": 1},
                "total": {"$sum": "$total"},
            }}
        ]
        return list(cls._col().aggregate(pipeline))


class Repartidor:
    """
    Subconjunto del modelo Usuario con extras de delivery.
    Los repartidores viven en la colección 'usuarios' con rol '5'.
    Esta clase provee métodos de consulta específicos.
    """

    @staticmethod
    def _col():
        return db["usuarios"]

    @classmethod
    def listar_activos(cls, tenant_id=None):
        q = {"usuario_rol": "5", "usuario_status": 1}
        if tenant_id:
            q["tenant_id"] = tenant_id
        return list(cls._col().find(q).sort("usuario_nombre", 1))

    @classmethod
    def get_by_id(cls, uid):
        return cls._col().find_one({"_id": ObjectId(uid), "usuario_rol": "5"})

    @classmethod
    def listar_todos(cls, tenant_id=None):
        q = {"usuario_rol": "5"}
        if tenant_id:
            q["tenant_id"] = tenant_id
        return list(cls._col().find(q).sort("usuario_nombre", 1))
