from flask import jsonify, session
from datetime import datetime, time
from config.db import db
from bson import ObjectId

class PropinasController:

    @staticmethod
    def propinas_hoy():
        try:
            mesero_id = session.get("usuario_id")
            if not mesero_id:
                return jsonify({"success": False}), 401

            mesero_id = ObjectId(mesero_id)

            cursor = db.comandas.find({
                "estado": "pagada",
                "mesero_id": mesero_id
            }).sort("fecha_cierre", -1)

            total = tarjeta = efectivo = 0
            lista = []

            for c in cursor:
                propina = float(c.get("propina") or 0)
                total_cuenta = float(c.get("total_final") or 0)
                metodo = c.get("metodo_pago", "EFECTIVO").upper()

                total += propina
                if metodo == "TARJETA":
                    tarjeta += propina
                else:
                    efectivo += propina

                fecha = c.get("fecha_cierre")
                hora = fecha.strftime("%H:%M") if fecha else "--:--"

                lista.append({
                    "hora": hora,
                    "mesa": c.get("mesa_numero"),
                    "total_cuenta": total_cuenta,
                    "metodo": metodo,
                    "monto": propina
                })

            return jsonify({
                "success": True,
                "total": total,
                "tarjeta": tarjeta,
                "efectivo": efectivo,
                "lista": lista
            })

        except Exception as e:
            print("❌ ERROR PROPINAS:", e)
            return jsonify({"success": False}), 500
