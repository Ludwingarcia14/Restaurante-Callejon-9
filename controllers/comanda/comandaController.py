from flask import jsonify, request, session, render_template
from models.comanda_model import Comanda
from config.db import db
from bson.objectid import ObjectId

class ComandaController:

    @staticmethod
    def comandas_activas():
        mesero_id = session.get("user_id")

        query = {
            "estado": {"$ne": "pagada"},
            "mesero_id": mesero_id
        }

        cursor = db.comandas.find(query).sort("fecha_apertura", -1)
        comandas = list(cursor)

        for c in comandas:
            c["_id"] = str(c["_id"])
            c["total"] = float(c.get("total", 0))

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
        mesero_id = session.get("user_id")

        if not numero_mesa or not num_comensales:
            return jsonify({"success": False, "error": "Datos incompletos"}), 400

        cuenta_id = Comanda.crear_comanda(numero_mesa, num_comensales, mesero_id)

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
