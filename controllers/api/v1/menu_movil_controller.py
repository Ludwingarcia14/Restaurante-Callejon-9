"""
Menú para la app móvil.
No requiere auth — cualquiera puede ver el menú.
"""
import logging
from flask import request, jsonify
from models.menu_model import Platillo
from utils.pagination import get_pagination_params, paginate_response
from utils.response import serialize_doc

logger = logging.getLogger(__name__)

CATEGORIAS_VALIDAS = {"entrada", "plato_fuerte", "bebida", "postre", "especial"}


class MenuMovilController:

    @staticmethod
    def get_menu():
        """
        GET /api/v1/menu
        Parámetros opcionales: ?categoria=bebida&buscar=tacos&page=1&limit=20
        Solo devuelve platillos disponibles=True.
        """
        categoria = request.args.get("categoria", "").strip().lower()
        buscar    = request.args.get("buscar", "").strip()
        limit, page, skip = get_pagination_params(default_limit=30, max_limit=100)

        query = {"disponible": True}

        if categoria and categoria in CATEGORIAS_VALIDAS:
            query["categoria"] = categoria

        if buscar:
            query["$or"] = [
                {"nombre":      {"$regex": buscar, "$options": "i"}},
                {"descripcion": {"$regex": buscar, "$options": "i"}},
            ]

        try:
            total    = Platillo.collection.count_documents(query)
            platillos = list(
                Platillo.collection.find(query)
                .sort("nombre", 1)
                .skip(skip)
                .limit(limit)
            )
        except Exception as e:
            logger.error("Error obteniendo menú: %s", e)
            return jsonify({"status": "error", "message": "Error al obtener el menú"}), 500

        data = [_serializar_platillo(p) for p in platillos]
        return jsonify({
            "status": "success",
            **paginate_response(data, total, page, limit),
        }), 200

    @staticmethod
    def get_platillo(platillo_id: str):
        """
        GET /api/v1/menu/<platillo_id>
        Detalle de un platillo específico.
        """
        try:
            platillo = Platillo.find_by_id(platillo_id)
        except Exception:
            return jsonify({"status": "error", "message": "ID inválido"}), 400

        if not platillo:
            return jsonify({"status": "error", "message": "Platillo no encontrado"}), 404

        if not platillo.get("disponible", True):
            return jsonify({"status": "error", "message": "Platillo no disponible"}), 404

        return jsonify({"status": "success", "data": _serializar_platillo(platillo)}), 200

    @staticmethod
    def get_categorias():
        """
        GET /api/v1/menu/categorias
        Lista las categorías que tienen al menos un platillo disponible.
        """
        try:
            pipeline = [
                {"$match": {"disponible": True}},
                {"$group": {"_id": "$categoria", "total": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ]
            resultado = list(Platillo.collection.aggregate(pipeline))
        except Exception as e:
            logger.error("Error obteniendo categorías: %s", e)
            return jsonify({"status": "error", "message": "Error al obtener categorías"}), 500

        nombres = Platillo.NOMBRE_CATEGORIAS
        categorias = [
            {
                "slug": r["_id"],
                "nombre": nombres.get(r["_id"], r["_id"]),
                "total": r["total"],
            }
            for r in resultado
            if r["_id"]
        ]
        return jsonify({"status": "success", "data": categorias}), 200


def _serializar_platillo(p: dict) -> dict:
    return {
        "id": str(p["_id"]),
        "nombre": p.get("nombre", ""),
        "descripcion": p.get("descripcion", ""),
        "categoria": p.get("categoria", ""),
        "categoria_nombre": Platillo.NOMBRE_CATEGORIAS.get(p.get("categoria", ""), ""),
        "precio": float(p.get("precio", 0)),
        "imagen": p.get("imagen", ""),
        "tiempo_preparacion": p.get("tiempo_preparacion", 15),
        "nivel_picante": p.get("nivel_picante", 0),
        "alergenos": p.get("alergenos", []),
        "disponible": p.get("disponible", True),
    }
