from flask import jsonify, session
from config.db import db
from bson.objectid import ObjectId

class MesaController:

    @staticmethod
    def estado_mesas_mesero():
        perfil_mesero = session.get("perfil_mesero")
        if not perfil_mesero:
            return jsonify({"success": False, "error": "Sesión inválida"}), 401

        mesas_asignadas = perfil_mesero.get("mesas_asignadas", [])

        mesas = {}
        cursor = db.mesas.find({"numero": {"$in": mesas_asignadas}})

        for m in cursor:
            mesas[m["numero"]] = {
                "estado": m.get("estado", "libre").lower(),
                "comensales": m.get("comensales", 0)
            }

        return jsonify({
            "success": True,
            "mesas": mesas
        })

    @staticmethod
    def detalle_mesa(numero):
        mesa = db.mesas.find_one({"numero": int(numero)})
        if not mesa:
            return jsonify({"success": False, "error": "Mesa no encontrada"}), 404

        mesa_data = {
            "numero": mesa["numero"],
            "estado": mesa.get("estado", "libre"),
            "comensales": mesa.get("comensales", 0),
            "cuenta_activa_id": str(mesa.get("cuenta_activa_id")) if mesa.get("cuenta_activa_id") else None
        }

        comanda_data = None
        cuenta_id = mesa.get("cuenta_activa_id")

        if cuenta_id:
            comanda = db.comandas.find_one({"_id": cuenta_id})
            if comanda:
                comanda_data = {
                    "folio": comanda.get("folio"),
                    "total": float(comanda.get("total", 0)),
                    "items": comanda.get("items", []),
                    "num_comensales": int(comanda.get("num_comensales", mesa.get("comensales", 0)))
                }

        return jsonify({
            "success": True,
            "mesa": mesa_data,
            "comanda": comanda_data
        })
