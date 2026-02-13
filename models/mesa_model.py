from config.db import db
from datetime import datetime
from bson.objectid import ObjectId


class Mesa:
    @staticmethod
    def _collection():
        if db is None:
            raise RuntimeError("❌ La base de datos Mongo no está inicializada")
        return db["mesas"]

    @staticmethod
    def _filtro_activa():
        return {
            "$or": [
                {"activa": True},
                {"activa": {"$exists": False}},
            ]
        }

    # =====================================================
    # CONSULTAS BÁSICAS (Ajustadas para tipos mixtos)
    # =====================================================
    @classmethod
    def find_all(cls):
        return list(cls._collection().find(cls._filtro_activa()))

    @classmethod
    def find_by_numero(cls, numero):
        """
        Busca una sola mesa por su número. 
        Soporta que el número llegue como string o entero.
        """
        try:
            # Buscamos intentando ambos tipos de datos para evitar errores de coincidencia
            query = {"numero": {"$in": [int(numero), str(numero)]}}
            return cls._collection().find_one(query)
        except Exception as e:
            print(f"❌ Error en find_by_numero: {e}")
            return None

    @classmethod
    def find_by_mesero(cls, mesero_id):
        """
        Busca todas las mesas asignadas a un mesero específico.
        """
        try:
            return list(cls._collection().find({"mesero_id": str(mesero_id)}))
        except Exception as e:
            print(f"❌ Error en find_by_mesero: {e}")
            return []
    @classmethod
    def find_by_numeros(cls, numeros_list):
        """
        Busca todas las mesas cuyos números estén en la lista proporcionada.
        """
        try:
            if not numeros_list:
                return []
            
            # Creamos una lista que contenga los números como int y como str 
            # para asegurar que encuentre la mesa sin importar el tipo en la DB
            busqueda = []
            for n in numeros_list:
                try:
                    busqueda.append(int(n))
                    busqueda.append(str(n))
                except:
                    busqueda.append(str(n))

            query = {"numero": {"$in": busqueda}}
            return list(cls._collection().find(query))
        except Exception as e:
            print(f"❌ Error en find_by_numeros: {e}")
            return []
    # =====================================================
    # ESTADO DE MESAS PARA DASHBOARD
    # =====================================================
    @classmethod
    def get_estado_mesas_mesero(cls, mesero_id=None, lista_numeros=None):
        if lista_numeros:
            mesas = cls.find_by_numeros(lista_numeros)
        elif mesero_id:
            mesas = cls.find_by_mesero(mesero_id)
        else:
            return {}

        estado_mesas = {}
        for mesa in mesas:
            # FORZAR LLAVE COMO STRING
            n_mesa = str(mesa.get("numero"))
            estado_mesas[n_mesa] = {
                "id": str(mesa.get("_id")),
                "numero": mesa.get("numero"),
                "estado": str(mesa.get("estado", "disponible")).lower(), # Forzar minúsculas
                "comensales": mesa.get("comensales", 0),
                "total": float(mesa.get("total", 0.0))
            }
        return estado_mesas

    # =====================================================
    # ACTUALIZACIÓN
    # =====================================================
    @classmethod
    def update_estado(cls, numero, nuevo_estado, cuenta_id=None):
        mesa_doc = cls.find_by_numero(numero)
        if not mesa_doc:
            return None

        update = {
            "estado": nuevo_estado,
            "updated_at": datetime.utcnow(),
        }

        if cuenta_id:
            update["cuenta_activa_id"] = str(cuenta_id)
        elif nuevo_estado in ("disponible", "limpieza"):
            update["cuenta_activa_id"] = None

        return cls._collection().update_one(
            {"_id": mesa_doc["_id"]},
            {"$set": update},
        )

    @classmethod
    def ocupar_mesa(cls, numero, cuenta_id):
        return cls.update_estado(numero, "ocupada", cuenta_id)

    @classmethod
    def liberar_mesa(cls, numero):
        return cls._collection().update_one(
            {"numero": str(numero)},
            {
                "$set": {
                    "estado": "limpieza",
                    "cuenta_activa_id": None,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

    @classmethod
    def marcar_disponible(cls, numero):
        return cls._collection().update_one(
            {"numero": str(numero)},
            {
                "$set": {
                    "estado": "disponible",
                    "cuenta_activa_id": None,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

    # =====================================================
    # ASIGNACIÓN DE MESERO
    # =====================================================
    @classmethod
    def asignar_mesero(cls, numero, mesero_id):
        return cls._collection().update_one(
            {"numero": str(numero)},
            {
                "$set": {
                    "mesero_id": mesero_id,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

    @classmethod
    def desasignar_mesero(cls, numero):
        return cls._collection().update_one(
            {"numero": str(numero)},
            {
                "$unset": {"mesero_id": ""},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )

    # =====================================================
    # RESERVAS
    # =====================================================
    @classmethod
    def crear_reserva(cls, numero, nombre, telefono, hora):
        return cls._collection().update_one(
            {"numero": str(numero)},
            {
                "$set": {
                    "estado": "reservada",
                    "reserva_nombre": nombre,
                    "reserva_telefono": telefono,
                    "reserva_hora": hora,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

    @classmethod
    def cancelar_reserva(cls, numero):
        return cls._collection().update_one(
            {"numero": str(numero)},
            {
                "$set": {
                    "estado": "disponible",
                    "updated_at": datetime.utcnow(),
                },
                "$unset": {
                    "reserva_nombre": "",
                    "reserva_telefono": "",
                    "reserva_hora": "",
                },
            },
        )

    # =====================================================
    # SERIALIZACIÓN
    # =====================================================
    @classmethod
    def to_dict(cls, mesa_doc):
        if not mesa_doc:
            return None

        data = {
            "id": str(mesa_doc["_id"]),
            "numero": mesa_doc.get("numero"),
            "capacidad": mesa_doc.get("capacidad", 0),
            "estado": mesa_doc.get("estado", "disponible"),
            "tipo": mesa_doc.get("tipo", "interior"),
            "seccion": mesa_doc.get("seccion", ""),
            "activa": mesa_doc.get("activa", True),
            "cuenta_activa_id": mesa_doc.get("cuenta_activa_id"),
            "created_at": mesa_doc.get("created_at"),
            "updated_at": mesa_doc.get("updated_at"),
        }

        if "mesero_id" in mesa_doc:
            data["mesero_id"] = mesa_doc["mesero_id"]

        if mesa_doc.get("estado") == "reservada":
            data.update(
                {
                    "reserva_nombre": mesa_doc.get("reserva_nombre"),
                    "reserva_hora": mesa_doc.get("reserva_hora"),
                    "reserva_telefono": mesa_doc.get("reserva_telefono"),
                }
            )

        return data

    # =====================================================
    # ESTADÍSTICAS
    # =====================================================
    @classmethod
    def get_estadisticas(cls):
        pipeline = [
            {"$match": cls._filtro_activa()},
            {"$group": {"_id": "$estado", "count": {"$sum": 1}}},
        ]

        resultado = list(cls._collection().aggregate(pipeline))

        stats = {
            "total": cls._collection().count_documents(cls._filtro_activa()),
            "disponibles": 0,
            "ocupadas": 0,
            "reservadas": 0,
            "limpieza": 0,
        }

        for r in resultado:
            if r["_id"] in stats:
                stats[r["_id"]] = r["count"]

        return stats
