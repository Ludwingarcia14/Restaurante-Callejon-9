from config.db import db
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from models.comanda_model import Comanda
from models.ticket_model import Ticket


class ComandaService:

    @staticmethod
    def get_activas(mesero_id: str) -> list:
        cursor = db.comandas.find({
            "estado": {"$nin": ["pagada", "cerrada"]},
            "mesero_id": ObjectId(mesero_id)
        }).sort("fecha_apertura", -1)

        comandas = []
        for c in cursor:
            c["id"] = str(c["_id"])
            c["_id"] = str(c["_id"])
            c["mesero_id"] = str(c["mesero_id"])
            for item in c.get("items", []):
                if "id" in item:
                    item["id"] = str(item["id"])
            c["total"] = float(c.get("total", 0))
            comandas.append(c)
        return comandas

    @staticmethod
    def abrir_cuenta(numero_mesa: int, num_comensales: int, mesero_id: str, mesero_nombre: str) -> str:
        cuenta_id = Comanda.crear_comanda(numero_mesa, num_comensales, mesero_id, mesero_nombre)
        db.mesas.update_one(
            {"numero": int(numero_mesa)},
            {"$set": {
                "estado": "ocupada",
                "cuenta_activa_id": ObjectId(cuenta_id),
                "comensales": int(num_comensales)
            }}
        )
        return cuenta_id

    @staticmethod
    def fusionar_items(items_existentes: list, items_nuevos: list) -> tuple:
        items_para_cocina = []
        for item_nuevo in items_nuevos:
            producto_id = item_nuevo.get("id")
            encontrado = False
            for item_existente in items_existentes:
                item_id = item_existente.get("producto_id") or item_existente.get("id")
                if str(item_id) == str(producto_id):
                    item_existente["cantidad"] += item_nuevo["cantidad"]
                    item_existente["estado_cocina"] = "pendiente"
                    items_para_cocina.append(producto_id)
                    encontrado = True
                    break
            if not encontrado:
                items_existentes.append({
                    "producto_id": producto_id,
                    "id": producto_id,
                    "nombre": item_nuevo["nombre"],
                    "precio": item_nuevo["precio"],
                    "cantidad": item_nuevo["cantidad"],
                    "estado_cocina": "pendiente",
                    "fecha_pedido": datetime.utcnow()
                })
                items_para_cocina.append(producto_id)
        return items_existentes, items_para_cocina

    @staticmethod
    def calcular_total(items: list) -> float:
        return sum(float(i.get("precio", 0)) * int(i.get("cantidad", 0)) for i in items)

    @staticmethod
    def guardar_items(cuenta_id: str, items_nuevos: list) -> dict:
        comanda = db.comandas.find_one({"_id": ObjectId(cuenta_id)})
        if not comanda:
            return {"success": False, "error": "Comanda no encontrada", "status": 404}

        items_existentes, items_para_cocina = ComandaService.fusionar_items(
            comanda.get("items", []), items_nuevos
        )
        total = ComandaService.calcular_total(items_existentes)

        db.comandas.update_one(
            {"_id": ObjectId(cuenta_id)},
            {"$set": {
                "items": items_existentes,
                "total": total,
                "estado": "enviada",
                "fecha_actualizacion": datetime.utcnow()
            }}
        )

        if items_para_cocina:
            _notificar_cocina(
                comanda_id=cuenta_id,
                mesa_numero=comanda.get("mesa_numero"),
                items=items_nuevos,
                mesero_nombre=comanda.get("mesero_nombre", "Mesero")
            )

        return {
            "success": True,
            "total": total,
            "items_count": len(items_existentes),
            "items_nuevos": len(items_para_cocina)
        }

    @staticmethod
    def calcular_propina(total: float, tipo_propina: str, custom_porcentaje=None) -> tuple:
        porcentaje = 0.0
        if tipo_propina == "custom":
            porcentaje = float(custom_porcentaje or 0)
        elif tipo_propina and str(tipo_propina).isdigit():
            porcentaje = float(tipo_propina)
        return round(total * (porcentaje / 100), 2), porcentaje

    @staticmethod
    def cerrar_cuenta(cuenta_id: str, metodo_pago: str, tipo_propina: str, custom_porcentaje=None) -> dict:
        comanda = db.comandas.find_one({"_id": ObjectId(cuenta_id)})
        if not comanda:
            return {"success": False, "error": "Comanda no encontrada", "status": 404}
        if comanda.get("estado") in ["cerrada", "pagada"]:
            return {"success": False, "error": "Esta cuenta ya fue cerrada", "status": 400}

        total = float(comanda.get("total", 0))
        propina, porcentaje = ComandaService.calcular_propina(total, tipo_propina, custom_porcentaje)
        total_final = round(total + propina, 2)
        fecha_actual = datetime.now()

        db.comandas.update_one(
            {"_id": ObjectId(cuenta_id)},
            {"$set": {
                "estado": "pagada",
                "metodo_pago": metodo_pago,
                "propina": propina,
                "porcentaje_propina": porcentaje,
                "total_final": total_final,
                "fecha_cierre": fecha_actual
            }}
        )

        mesa_numero = comanda.get("mesa_numero")
        db.mesas.update_one(
            {"numero": mesa_numero},
            {"$set": {
                "estado": "disponible",
                "cuenta_activa_id": None,
                "num_comensales": 0,
                "ultima_actualizacion": fecha_actual
            }}
        )

        if propina > 0 and comanda.get("mesero_id"):
            db.propinas.insert_one({
                "mesero_id": comanda.get("mesero_id"),
                "comanda_id": ObjectId(cuenta_id),
                "mesa_numero": mesa_numero,
                "monto": propina,
                "porcentaje": porcentaje,
                "fecha": fecha_actual,
                "metodo_pago": metodo_pago
            })

        Ticket.create(
            comanda=comanda,
            metodo_pago=metodo_pago,
            propina=propina,
            porcentaje_propina=porcentaje,
            total_final=total_final,
            fecha_cierre=fecha_actual,
        )

        return {
            "success": True,
            "total": total,
            "propina": propina,
            "porcentaje_propina": porcentaje,
            "total_final": total_final
        }

    @staticmethod
    def estadisticas_dia(mesero_id: str) -> dict:
        inicio_dia = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        fin_dia = inicio_dia + timedelta(days=1)

        cursor = db.comandas.find({
            "estado": {"$in": ["pagada", "cerrada"]},
            "mesero_id": ObjectId(mesero_id),
            "fecha_cierre": {"$gte": inicio_dia, "$lt": fin_dia}
        })

        venta, propinas, ordenes = 0.0, 0.0, 0
        for c in cursor:
            venta += float(c.get("total_final", 0))
            propinas += float(c.get("propina", 0))
            ordenes += 1

        return {"venta_dia": venta, "propinas_dia": propinas, "num_ordenes": ordenes}

    @staticmethod
    def get_cerradas(mesero_id: str) -> list:
        cursor = db.comandas.find({
            "estado": {"$in": ["pagada", "cerrada"]},
            "mesero_id": ObjectId(mesero_id)
        }).sort("fecha_cierre", -1)

        return [{
            "id": str(c["_id"]),
            "folio": c.get("folio"),
            "mesa": c.get("mesa_numero"),
            "total": float(c.get("total", 0)),
            "propina": float(c.get("propina", 0)),
            "total_final": float(c.get("total_final", c.get("total", 0))),
            "metodo_pago": c.get("metodo_pago"),
            "fecha": c.get("fecha_cierre")
        } for c in cursor]


# ── Funciones de notificación (privadas al módulo) ──────────────────────────

def _notificar_cocina(comanda_id, mesa_numero, items, mesero_nombre):
    try:
        from extensions import socketio
        socketio.emit(
            "nuevo_pedido",
            {
                "comanda_id": comanda_id,
                "mesa": mesa_numero,
                "items": items,
                "mesero": mesero_nombre,
                "timestamp": datetime.utcnow().isoformat(),
                "num_items": len(items)
            },
            room="cocina",
            namespace="/"
        )
        _crear_notificacion_bd_cocina(comanda_id, mesa_numero, items)
    except Exception as e:
        print(f"⚠️ Error al notificar a cocina: {e}")


def _crear_notificacion_bd_cocina(comanda_id, mesa_numero, items):
    try:
        for usuario in db.usuarios.find({"rol": 3}):
            db.notificaciones.insert_one({
                "id_usuario": usuario["_id"],
                "tipo": "nuevo_pedido",
                "titulo": f"Nuevo Pedido - Mesa {mesa_numero}",
                "mensaje": f"{len(items)} platillo(s) para preparar",
                "leida": False,
                "fecha": datetime.utcnow(),
                "datos": {"comanda_id": comanda_id, "mesa": mesa_numero, "items": items}
            })
    except Exception as e:
        print(f"⚠️ Error al crear notificación en BD: {e}")
