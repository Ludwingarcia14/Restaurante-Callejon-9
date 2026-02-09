from flask import jsonify, request, session, render_template
from models.comanda_model import Comanda
from config.db import db
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime, time, timedelta

class ComandaController:

    @staticmethod
    def comandas_activas():
        mesero_id = session.get("usuario_id")

        if not mesero_id:
            return jsonify({"success": True, "comandas": [], "total": 0})

        mesero_oid = ObjectId(mesero_id)

        cursor = db.comandas.find({
            "estado": {"$ne": "pagada"},
            "mesero_id": mesero_oid
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

        return jsonify({
            "success": True,
            "comandas": comandas,
            "total": len(comandas)
        })


    @staticmethod
    def abrir_cuenta():
        data = request.json
        numero_mesa = data.get("numero_mesa")
        num_comensales = data.get("num_comensales")
        mesero_id = session.get("usuario_id")

        if not mesero_id:
            return jsonify({
                "success": False,
                "error": "Sesión no válida"
            }), 401

        if not numero_mesa or not num_comensales:
            return jsonify({
                "success": False,
                "error": "Datos incompletos"
            }), 400

        cuenta_id = Comanda.crear_comanda(
            numero_mesa,
            num_comensales,
            mesero_id
        )

        db.mesas.update_one(
            {"numero": int(numero_mesa)},
            {"$set": {
                "estado": "ocupada",
                "cuenta_activa_id": ObjectId(cuenta_id),
                "comensales": int(num_comensales)
            }}
        )

        return jsonify({
            "success": True,
            "cuenta_id": cuenta_id,
            "message": "Cuenta abierta correctamente"
        })

    @staticmethod
    def guardar_items(cuenta_id):
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "No se recibieron datos"}), 400
        items = data.get("items", [])
        if not items:
            return jsonify({"success": False, "error": "Pedido vacío"}), 400
        Comanda.agregar_items(cuenta_id, items)
        return jsonify({
        "success": True,
        "message": "Pedido enviado a cocina"
    }), 200

    @staticmethod
    def vista_agregar_items(cuenta_id):
        perfil_mesero = session.get("perfil_mesero")
        return render_template(
            "mesero/mesero_menu.html",
            perfil=perfil_mesero,
            cuenta_id=cuenta_id
        )

    @staticmethod
    def cerrar_cuenta(cuenta_id):
        data = request.json or {}

        metodo_pago = data.get("metodo_pago", "efectivo")
        tipo_propina = data.get("tipo_propina", "sin")
        custom_porcentaje = data.get("custom_porcentaje")

        comanda = db.comandas.find_one({"_id": ObjectId(cuenta_id)})
        if not comanda:
            return jsonify({"success": False, "error": "Comanda no encontrada"}), 404

        total = float(comanda.get("total", 0))

        # ==========================
        # 🧮 CALCULAR PROPINA
        # ==========================
        porcentaje = 0

        if tipo_propina == "custom":
            porcentaje = float(custom_porcentaje or 0)
        elif tipo_propina.isdigit():
            porcentaje = float(tipo_propina)

        propina = round(total * (porcentaje / 100), 2)
        total_final = round(total + propina, 2)

        # ==========================
        # 💾 GUARDAR COMANDA
        # ==========================
        db.comandas.update_one(
            {"_id": ObjectId(cuenta_id)},
            {"$set": {
                "estado": "pagada",
                "metodo_pago": metodo_pago,
                "propina": propina,
                "porcentaje_propina": porcentaje,
                "total_final": total_final,
                "fecha_cierre": datetime.utcnow()
            }}
        )

        # ==========================
        # 🪑 LIBERAR MESA
        # ==========================
        db.mesas.update_one(
            {"cuenta_activa_id": ObjectId(cuenta_id)},
            {"$set": {
                "estado": "libre",
                "cuenta_activa_id": None,
                "comensales": 0
            }}
        )

        return jsonify({
            "success": True,
            "total": total,
            "propina": propina,
            "porcentaje": porcentaje,
            "total_final": total_final
        })

        
    @staticmethod
    def comandas_cerradas():
        mesero_id = session.get("usuario_id")

        if not mesero_id:
            return jsonify({"success": True, "comandas": []})

        try:
            mesero_oid = ObjectId(mesero_id)
        except Exception:
            return jsonify({"success": True, "comandas": []})

        cursor = db.comandas.find({
            "estado": "pagada",
            "mesero_id": mesero_oid
        }).sort("fecha_cierre", -1)

        comandas = []
        for c in cursor:
            comandas.append({
                "id": str(c["_id"]),
                "folio": c.get("folio"),
                "mesa": c.get("mesa_numero"),
                "total": float(c.get("total", 0)),
                "propina": float(c.get("propina", 0)),
                "total_final": float(c.get("total_final", c.get("total", 0))),
                "metodo_pago": c.get("metodo_pago"),
                "fecha": c.get("fecha_cierre")
            })

        return jsonify({
            "success": True,
            "comandas": comandas
        })
        
    @staticmethod
    def estadisticas_dia_mesero():
        mesero_id = session.get("usuario_id")
        if not mesero_id:
            return jsonify({"success": False}), 401

        mesero_oid = ObjectId(mesero_id)

        inicio_dia = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        fin_dia = inicio_dia + timedelta(days=1)

        cursor = db.comandas.find({
            "estado": "pagada",
            "mesero_id": mesero_oid,
            "fecha_cierre": {
                "$gte": inicio_dia,
                "$lt": fin_dia
            }
        })

        venta = 0
        propinas = 0
        ordenes = 0

        for c in cursor:
            venta += float(c.get("total_final", 0))
            propinas += float(c.get("propina", 0))
            ordenes += 1

        return jsonify({
            "success": True,
            "estadisticas": {
                "venta_dia": venta,
                "propinas_dia": propinas,
                "num_ordenes": ordenes
            }
        })