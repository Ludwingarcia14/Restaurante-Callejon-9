from flask import jsonify, request, session, render_template
from bson.errors import InvalidId
from bson.objectid import ObjectId
from services.comanda_service import ComandaService
from config.db import db


class ComandaController:

    @staticmethod
    def comandas_activas():
        mesero_id = session.get("usuario_id")
        if not mesero_id:
            return jsonify({"success": True, "comandas": [], "total": 0})
        comandas = ComandaService.get_activas(mesero_id)
        return jsonify({"success": True, "comandas": comandas, "total": len(comandas)})

    @staticmethod
    def abrir_cuenta():
        data = request.json or {}
        numero_mesa = data.get("numero_mesa")
        num_comensales = data.get("num_comensales")
        mesero_id = session.get("usuario_id")

        if not mesero_id:
            return jsonify({"success": False, "error": "Sesión no válida"}), 401
        if not numero_mesa or not num_comensales:
            return jsonify({"success": False, "error": "Datos incompletos"}), 400

        cuenta_id = ComandaService.abrir_cuenta(
            numero_mesa, num_comensales, mesero_id, session.get("usuario_nombre", "Mesero")
        )
        return jsonify({"success": True, "cuenta_id": cuenta_id, "message": "Cuenta abierta correctamente"})

    @staticmethod
    def guardar_items(cuenta_id):
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "No se recibieron datos"}), 400
        items_nuevos = data.get("items", [])
        if not items_nuevos:
            return jsonify({"success": False, "error": "Pedido vacío"}), 400

        try:
            result = ComandaService.guardar_items(cuenta_id, items_nuevos)
            if not result["success"]:
                return jsonify(result), result.get("status", 400)
            return jsonify({
                "success": True,
                "message": "Pedido enviado a cocina",
                "total": result["total"],
                "items_count": result["items_count"],
                "items_nuevos": result["items_nuevos"]
            }), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def vista_agregar_items(cuenta_id):
        return render_template(
            "mesero/mesero_menu.html",
            perfil=session.get("perfil_mesero"),
            cuenta_id=cuenta_id
        )

    @staticmethod
    def cerrar_cuenta(cuenta_id):
        data = request.json or {}
        metodo_pago = data.get("metodo_pago", "efectivo")
        tipo_propina = data.get("tipo_propina", "sin")
        custom_porcentaje = data.get("custom_porcentaje")

        try:
            result = ComandaService.cerrar_cuenta(cuenta_id, metodo_pago, tipo_propina, custom_porcentaje)
            if not result["success"]:
                return jsonify(result), result.get("status", 400)
            return jsonify({**result, "message": "Cuenta cerrada correctamente"})
        except InvalidId:
            return jsonify({"success": False, "error": "ID de cuenta inválido"}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def verificar_estado_pago(cuenta_id):
        try:
            cuenta_oid = ObjectId(cuenta_id)
        except Exception:
            return jsonify({"success": False, "error": "ID inválido"}), 400

        comanda = db.comandas.find_one({"_id": cuenta_oid})
        if not comanda:
            return jsonify({"success": False, "error": "Comanda no encontrada"}), 404

        if comanda.get("estado") in ["cerrada", "pagada"]:
            return jsonify({
                "success": True,
                "status": "approved",
                "total": float(comanda.get("total_final", comanda.get("total", 0))),
                "propina": float(comanda.get("propina", 0)),
                "metodo_pago": comanda.get("metodo_pago", "efectivo")
            })
        return jsonify({"success": True, "status": "pending"})

    @staticmethod
    def comandas_cerradas():
        mesero_id = session.get("usuario_id")
        if not mesero_id:
            return jsonify({"success": True, "comandas": []})
        try:
            return jsonify({"success": True, "comandas": ComandaService.get_cerradas(mesero_id)})
        except Exception:
            return jsonify({"success": True, "comandas": []})

    @staticmethod
    def estadisticas_dia_mesero():
        mesero_id = session.get("usuario_id")
        if not mesero_id:
            return jsonify({"success": False}), 401
        stats = ComandaService.estadisticas_dia(mesero_id)
        return jsonify({"success": True, "estadisticas": stats})
