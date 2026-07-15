from config.db import db
from datetime import datetime
from bson.objectid import ObjectId


class SensorData:

    @staticmethod
    def _col():
        return db["sensor_data"]

    @classmethod
    def guardar(cls, data):
        doc = {
            "repartidor_id":     data.get("repartidor_id", ""),
            "repartidor_nombre": data.get("repartidor_nombre", ""),
            "lat":               float(data.get("lat") or 0),
            "lon":               float(data.get("lon") or 0),
            "battery":           float(data.get("battery") or 0),
            "pasos":             int(data.get("pasos") or 0),
            "tenant_id":         data.get("tenant_id", ""),
            "timestamp":         datetime.utcnow(),
        }
        res = cls._col().insert_one(doc)
        return str(res.inserted_id)

    @classmethod
    def ultimo_por_repartidor(cls, repartidor_id):
        return cls._col().find_one(
            {"repartidor_id": str(repartidor_id)},
            sort=[("timestamp", -1)]
        )

    @classmethod
    def todos_activos(cls, tenant_id=None):
        """Última lectura de sensor por repartidor."""
        pipeline = []
        if tenant_id:
            pipeline.append({"$match": {"tenant_id": tenant_id}})
        pipeline += [
            {"$sort": {"timestamp": -1}},
            {"$group": {"_id": "$repartidor_id", "doc": {"$first": "$$ROOT"}}},
            {"$replaceRoot": {"newRoot": "$doc"}},
            {"$sort": {"repartidor_nombre": 1}},
        ]
        return list(cls._col().aggregate(pipeline))

    @classmethod
    def historial(cls, tenant_id=None, repartidor_id=None, limit=100):
        q = {}
        if tenant_id:
            q["tenant_id"] = tenant_id
        if repartidor_id:
            q["repartidor_id"] = str(repartidor_id)
        return list(cls._col().find(q).sort("timestamp", -1).limit(limit))
