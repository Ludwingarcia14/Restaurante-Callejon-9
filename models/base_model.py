"""
Modelo base con aislamiento multi-tenant.

Centraliza el acceso a una coleccion de Mongo inyectando automaticamente el
`tenant_id` activo en cada consulta y en cada documento creado. Es el unico
lugar donde se hace cumplir el aislamiento entre restaurantes, por lo que las
subclases NO deben consultar `collection` directamente sin pasar por aqui.

No importa la conexion a la base de datos: cada subclase asigna su propia
`collection` (p.ej. `collection = db["ventas"]`). Esto mantiene la logica de
scoping probable sin Mongo.
"""
from bson.objectid import ObjectId

from utils.tenant_context import require_current_tenant


class BaseModel:
    collection = None

    @classmethod
    def _scoped(cls, filtro=None):
        """Devuelve un dict con el tenant activo incluido (filtro o documento)."""
        scoped = dict(filtro or {})
        scoped["tenant_id"] = require_current_tenant()
        return scoped

    @classmethod
    def find_all(cls, filtro=None):
        return list(cls.collection.find(cls._scoped(filtro)))

    @classmethod
    def find_by_id(cls, id):
        return cls.collection.find_one(cls._scoped({"_id": ObjectId(id)}))

    @classmethod
    def create(cls, data):
        return cls.collection.insert_one(cls._scoped(data))
