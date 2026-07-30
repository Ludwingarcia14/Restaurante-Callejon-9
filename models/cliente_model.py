"""
Modelo de Cliente — usuario de la app móvil.
Separado del modelo Empleado; no tiene acceso al panel web.
"""
import hashlib
from config.db import db
from datetime import datetime
from bson.objectid import ObjectId


class Cliente:
    collection = db["clientes"]

    # =========================================================
    # CONSULTAS
    # =========================================================

    @classmethod
    def find_by_email(cls, email: str):
        return cls.collection.find_one({"email": email.strip().lower()})

    @classmethod
    def find_by_id(cls, cliente_id: str):
        try:
            return cls.collection.find_one({"_id": ObjectId(cliente_id)})
        except Exception:
            return None

    # =========================================================
    # COMANDOS
    # =========================================================

    @classmethod
    def create(cls, nombre: str, apellidos: str, email: str,
               password_hash: str, telefono: str = "", tenant_id: str = None) -> str:
        now = datetime.utcnow()
        doc = {
            "nombre": nombre.strip(),
            "apellidos": apellidos.strip(),
            "email": email.strip().lower(),
            "password": password_hash,
            "telefono": telefono.strip(),
            "foto_url": "",
            "tipo": "cliente",
            "activo": True,
            "puntos": 0,
            # Opcional: permite ubicar al cliente en un restaurante especifico
            # en despliegues multi-tenant. None en despliegues de un solo restaurante.
            "tenant_id": tenant_id.strip() if isinstance(tenant_id, str) and tenant_id.strip() else None,
            "refresh_token_hash": None,
            "created_at": now,
            "updated_at": now,
        }
        result = cls.collection.insert_one(doc)
        return str(result.inserted_id)

    @classmethod
    def update_perfil(cls, cliente_id: str, campos: dict):
        campos["updated_at"] = datetime.utcnow()
        return cls.collection.update_one(
            {"_id": ObjectId(cliente_id)},
            {"$set": campos}
        )

    @classmethod
    def update_password(cls, cliente_id: str, new_hash: str):
        return cls.collection.update_one(
            {"_id": ObjectId(cliente_id)},
            {"$set": {"password": new_hash, "updated_at": datetime.utcnow()}}
        )

    @classmethod
    def set_tenant_id(cls, cliente_id: str, tenant_id: str):
        """
        Asigna el restaurante (tenant) a un cliente que aún no lo tenía.
        Usado para clientes registrados antes de que el registro resolviera
        automáticamente el restaurante por defecto.
        """
        return cls.collection.update_one(
            {"_id": ObjectId(cliente_id)},
            {"$set": {"tenant_id": tenant_id, "updated_at": datetime.utcnow()}}
        )

    @classmethod
    def update_refresh_token(cls, cliente_id: str, token_hash):
        """Almacena el SHA-256 del refresh token (o None en logout)."""
        return cls.collection.update_one(
            {"_id": ObjectId(cliente_id)},
            {"$set": {"refresh_token_hash": token_hash, "updated_at": datetime.utcnow()}}
        )

    # =========================================================
    # SERIALIZACIÓN
    # =========================================================

    @classmethod
    def to_public(cls, doc: dict) -> dict:
        if not doc:
            return {}
        created = doc.get("created_at")
        return {
            "id": str(doc["_id"]),
            "nombre": doc.get("nombre", ""),
            "apellidos": doc.get("apellidos", ""),
            "email": doc.get("email", ""),
            "telefono": doc.get("telefono", ""),
            "foto_url": doc.get("foto_url", ""),
            "rol": "cliente",
            "tenant_id": doc.get("tenant_id"),
            "puntos": doc.get("puntos", 0),
            "created_at": created.isoformat() if created else None,
        }

    # =========================================================
    # ÍNDICES (llamar una vez al arrancar la app)
    # =========================================================

    @classmethod
    def ensure_indexes(cls):
        cls.collection.create_index("email", unique=True)
