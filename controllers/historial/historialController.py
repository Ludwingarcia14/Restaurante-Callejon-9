from flask import jsonify, session, request
from datetime import datetime, time
from config.db import db
from bson import ObjectId
class HistorialController:

    @staticmethod
    def historial_mesero():
        mesero_id = session.get("usuario_id")
        fecha_str = request.args.get("fecha")

        mesero_oid = ObjectId(mesero_id)

        fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
        inicio = datetime.combine(fecha.date(), time.min)
        fin = datetime.combine(fecha.date(), time.max)

        cursor = db.comandas.find({
            "estado": "pagada",
            "mesero_id": mesero_oid,
            "fecha_cierre": {
                "$gte": inicio,
                "$lte": fin
            }
        })

        total = 0
        registros = []

        for c in cursor:
            total += float(c.get("total_final") or 0)

            registros.append({
                "mesa_numero": c.get("mesa_numero"),
                "hora_cierre": c["fecha_cierre"].strftime("%H:%M"),
                "total": float(c.get("total_final") or 0),
                "metodo_pago": c.get("metodo_pago", "N/A").upper(),
                "estado": "PAGADO"
            })

        return jsonify({
            "success": True,
            "total_dia": total,
            "registros": registros
        })
