import math
from datetime import datetime

from bson import ObjectId
from flask import jsonify, request, session

from config.db import db


def _notificar_meseros_platillo_no_disponible(nombre_platillo, razon, usuario_cocina):
    try:
        from extensions import socketio
        from controllers.notificaciones.notificacion_controller import NotificacionCommandHandler

        mensaje = f"⚠️ \"{nombre_platillo}\" ya no está disponible — {razon}"

        # Emitir a todos los clientes conectados (el JS filtra por rol)
        socketio.emit(
            "platillo_no_disponible",
            {"nombre": nombre_platillo, "razon": razon, "usuario": usuario_cocina, "mensaje": mensaje},
            namespace="/",
        )

        # Crear notificación persistente en DB para cada mesero
        meseros = list(db.usuarios.find({"usuario_rol": "2"}, {"_id": 1}))
        for m in meseros:
            try:
                NotificacionCommandHandler.crear_notificacion(
                    tipo="PLATILLO_NO_DISPONIBLE",
                    mensaje=mensaje,
                    id_usuario=str(m["_id"]),
                    datos_extra={"platillo": nombre_platillo, "razon": razon},
                )
            except Exception:
                pass
    except Exception as e:
        print(f"[WARN] Error notificando meseros: {e}")


def _calcular_tiempo(fecha_inicio):
    if not fecha_inicio:
        return "Recién"
    delta = datetime.utcnow() - fecha_inicio
    minutos = int(delta.total_seconds() / 60)
    if minutos < 60:
        return f"{minutos} min"
    elif minutos < 1440:
        horas = minutos // 60
        return f"{horas} hora{'s' if horas > 1 else ''}"
    else:
        dias = minutos // 1440
        return f"{dias} día{'s' if dias > 1 else ''}"


class PlatillosNoDisponiblesController:

    @staticmethod
    def obtener_activos():
        try:
            docs = list(db.platillos_no_disponibles.find({"activo": True}).sort("fecha_registro", -1))
            data = [
                {
                    "id":                   str(d["_id"]),
                    "platillo_id":          d["platillo_id"],
                    "platillo_nombre":      d.get("platillo_nombre", "Desconocido"),
                    "razon":                d.get("razon", ""),
                    "fecha_registro":       d["fecha_registro"].strftime("%H:%M") if d.get("fecha_registro") else "",
                    "usuario_registro":     d.get("usuario_registro", "Sistema"),
                    "tiempo_no_disponible": _calcular_tiempo(d.get("fecha_registro")),
                }
                for d in docs
            ]
            return jsonify({"success": True, "data": data, "total": len(data)})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def obtener_todos():
        try:
            page             = int(request.args.get("page", 1))
            per_page         = int(request.args.get("per_page", 20))
            incluir_inactivos = request.args.get("incluir_inactivos", "false").lower() == "true"

            query = {} if incluir_inactivos else {"activo": True}
            total = db.platillos_no_disponibles.count_documents(query)
            skip  = (page - 1) * per_page
            docs  = list(
                db.platillos_no_disponibles.find(query)
                .sort("fecha_registro", -1)
                .skip(skip)
                .limit(per_page)
            )
            data = [
                {
                    "id":                  str(d["_id"]),
                    "platillo_id":         d["platillo_id"],
                    "platillo_nombre":     d.get("platillo_nombre", "Desconocido"),
                    "razon":               d.get("razon", ""),
                    "activo":              d.get("activo", False),
                    "usuario_registro":    d.get("usuario_registro", "Sistema"),
                    "fecha_registro":      d["fecha_registro"].strftime("%Y-%m-%d %H:%M:%S") if d.get("fecha_registro") else "",
                    "fecha_reactivacion":  d["fecha_reactivacion"].strftime("%Y-%m-%d %H:%M:%S") if d.get("fecha_reactivacion") else None,
                    "usuario_reactivacion": d.get("usuario_reactivacion"),
                }
                for d in docs
            ]
            return jsonify({
                "success":  True,
                "data":     data,
                "total":    total,
                "page":     page,
                "per_page": per_page,
                "pages":    math.ceil(total / per_page) if per_page else 1,
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def obtener_historial():
        try:
            pipeline = [
                {"$group": {
                    "_id":                       "$platillo_id",
                    "platillo_nombre":           {"$first": "$platillo_nombre"},
                    "veces_marcado":             {"$sum": 1},
                    "actualmente_no_disponible": {"$sum": {"$cond": ["$activo", 1, 0]}},
                }},
                {"$sort": {"veces_marcado": -1}},
            ]
            data = [
                {
                    "platillo_id":               d["_id"],
                    "platillo_nombre":           d.get("platillo_nombre", "Desconocido"),
                    "veces_marcado":             d["veces_marcado"],
                    "actualmente_no_disponible": d["actualmente_no_disponible"] > 0,
                }
                for d in db.platillos_no_disponibles.aggregate(pipeline)
            ]
            return jsonify({"success": True, "data": data})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def marcar_no_disponible():
        try:
            body       = request.get_json() or {}
            platillo_id = str(body.get("platillo_id", "")).strip()
            razon      = body.get("razon", "").strip()
            usuario    = session.get("usuario_nombre", "Sistema")

            if not platillo_id:
                return jsonify({"success": False, "error": "ID del platillo es requerido"}), 400
            if not razon:
                return jsonify({"success": False, "error": "Razón es requerida"}), 400

            try:
                platillo = db.platillos.find_one({"_id": ObjectId(platillo_id)})
            except Exception:
                platillo = None

            if not platillo:
                return jsonify({"success": False, "error": "Platillo no encontrado"}), 404

            if db.platillos_no_disponibles.find_one({"platillo_id": platillo_id, "activo": True}):
                return jsonify({"success": False, "error": f"El platillo \"{platillo['nombre']}\" ya está marcado como no disponible"}), 409

            ahora = datetime.utcnow()
            db.platillos_no_disponibles.insert_one({
                "platillo_id":      platillo_id,
                "platillo_nombre":  platillo["nombre"],
                "razon":            razon,
                "activo":           True,
                "fecha_registro":   ahora,
                "usuario_registro": usuario,
            })
            db.platillos.update_one({"_id": ObjectId(platillo_id)}, {"$set": {"disponible": False}})

            # Notificar a todos los meseros en tiempo real
            _notificar_meseros_platillo_no_disponible(platillo["nombre"], razon, usuario)

            return jsonify({"success": True, "message": f"Platillo \"{platillo['nombre']}\" marcado como no disponible"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def reactivar_platillo(platillo_id):
        try:
            platillo_id = str(platillo_id)
            usuario     = session.get("usuario_nombre", "Sistema")

            registro = db.platillos_no_disponibles.find_one({"platillo_id": platillo_id, "activo": True})
            if not registro:
                return jsonify({"success": False, "error": "El platillo no está marcado como no disponible"}), 404

            ahora = datetime.utcnow()
            db.platillos_no_disponibles.update_one(
                {"_id": registro["_id"]},
                {"$set": {"activo": False, "fecha_reactivacion": ahora, "usuario_reactivacion": usuario}},
            )
            try:
                db.platillos.update_one({"_id": ObjectId(platillo_id)}, {"$set": {"disponible": True}})
            except Exception:
                pass

            nombre = registro.get("platillo_nombre", "Platillo")
            return jsonify({"success": True, "message": f"Platillo \"{nombre}\" reactivado correctamente"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def obtener_platillos_activos():
        try:
            docs = list(db.platillos.find({"disponible": True}, {"nombre": 1}))
            data = [{"id": str(d["_id"]), "nombre": d["nombre"]} for d in docs]
            return jsonify({"success": True, "data": data})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @staticmethod
    def get_estadisticas():
        try:
            total_platillos  = db.platillos.count_documents({})
            no_disponibles   = db.platillos_no_disponibles.count_documents({"activo": True})
            total_registros  = db.platillos_no_disponibles.count_documents({})

            top_razones = [
                {"razon": r["_id"], "total": r["total"]}
                for r in db.platillos_no_disponibles.aggregate([
                    {"$group": {"_id": "$razon", "total": {"$sum": 1}}},
                    {"$sort":  {"total": -1}},
                    {"$limit": 5},
                ])
            ]
            return jsonify({
                "success": True,
                "data": {
                    "total_platillos":            total_platillos,
                    "no_disponibles":             no_disponibles,
                    "porcentaje_no_disponibles":  round(no_disponibles / total_platillos * 100, 2) if total_platillos else 0,
                    "total_registros_historicos": total_registros,
                    "top_razones":                top_razones,
                },
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
