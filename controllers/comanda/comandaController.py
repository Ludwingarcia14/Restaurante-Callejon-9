from flask import jsonify, request, session, render_template
from models.comanda_model import Comanda
from config.db import db
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime

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

        propina = float(data.get("propina", 0))
        metodo_pago = data.get("metodo_pago", "efectivo")

        comanda = db.comandas.find_one({"_id": ObjectId(cuenta_id)})
        if not comanda:
            return jsonify({"success": False, "error": "Comanda no encontrada"}), 404

        total = float(comanda.get("total", 0))
        total_final = total + propina

        db.comandas.update_one(
            {"_id": ObjectId(cuenta_id)},
            {"$set": {
                "estado": "pagada",
                "propina": propina,
                "metodo_pago": metodo_pago,
                "total_final": total_final,
                "fecha_cierre": datetime.utcnow()
            }}
        )

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

