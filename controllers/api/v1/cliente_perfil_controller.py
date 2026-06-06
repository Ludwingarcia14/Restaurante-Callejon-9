"""
Gestión del perfil del cliente autenticado.
Requiere jwt_required en todas las rutas.
"""
import logging
from flask import request, jsonify
from models.cliente_model import Cliente
from services.security.password_service import PasswordService
from utils.validators import sanitize_str

logger = logging.getLogger(__name__)


class ClientePerfilController:

    # ----------------------------------------------------------
    # VER PERFIL
    # ----------------------------------------------------------
    @staticmethod
    def get_perfil():
        cliente_id = request.jwt_payload["sub"]
        doc = Cliente.find_by_id(cliente_id)
        if not doc:
            return jsonify({"status": "error", "message": "Cliente no encontrado"}), 404
        return jsonify({"status": "success", "data": Cliente.to_public(doc)}), 200

    # ----------------------------------------------------------
    # ACTUALIZAR NOMBRE / APELLIDOS / TELÉFONO
    # ----------------------------------------------------------
    @staticmethod
    def actualizar_perfil():
        cliente_id = request.jwt_payload["sub"]
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Se requiere body JSON"}), 400

        campos = {}

        if "nombre" in data:
            nombre = sanitize_str(data["nombre"], 100)
            if not nombre:
                return jsonify({"status": "error", "message": "El nombre no puede estar vacío"}), 400
            campos["nombre"] = nombre

        if "apellidos" in data:
            campos["apellidos"] = sanitize_str(data["apellidos"], 100)

        if "telefono" in data:
            campos["telefono"] = sanitize_str(data["telefono"], 20)

        if not campos:
            return jsonify({"status": "error", "message": "No hay campos para actualizar"}), 400

        try:
            Cliente.update_perfil(cliente_id, campos)
        except Exception as e:
            logger.error("Error actualizando perfil: %s", e)
            return jsonify({"status": "error", "message": "Error al actualizar el perfil"}), 500

        doc = Cliente.find_by_id(cliente_id)
        return jsonify({
            "status": "success",
            "message": "Perfil actualizado",
            "data": Cliente.to_public(doc),
        }), 200

    # ----------------------------------------------------------
    # ACTUALIZAR FOTO
    # ----------------------------------------------------------
    @staticmethod
    def actualizar_foto():
        cliente_id = request.jwt_payload["sub"]
        data = request.get_json(silent=True)
        if not data or not data.get("foto_url"):
            return jsonify({"status": "error", "message": "foto_url es requerida"}), 400

        foto_url = sanitize_str(data["foto_url"], 500)
        if not foto_url.startswith(("http://", "https://")):
            return jsonify({"status": "error", "message": "foto_url debe ser una URL válida (http/https)"}), 400

        try:
            Cliente.update_perfil(cliente_id, {"foto_url": foto_url})
        except Exception as e:
            logger.error("Error actualizando foto: %s", e)
            return jsonify({"status": "error", "message": "Error al actualizar la foto"}), 500

        return jsonify({
            "status": "success",
            "message": "Foto de perfil actualizada",
            "foto_url": foto_url,
        }), 200

    # ----------------------------------------------------------
    # CAMBIAR CONTRASEÑA
    # ----------------------------------------------------------
    @staticmethod
    def cambiar_password():
        cliente_id = request.jwt_payload["sub"]
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Se requiere body JSON"}), 400

        password_actual = data.get("password_actual", "")
        password_nuevo  = data.get("password_nuevo", "")

        if not password_actual or not password_nuevo:
            return jsonify({"status": "error", "message": "password_actual y password_nuevo son requeridos"}), 400
        if len(password_nuevo) < 6:
            return jsonify({"status": "error", "message": "La nueva contraseña debe tener al menos 6 caracteres"}), 400
        if len(password_nuevo) > 128:
            return jsonify({"status": "error", "message": "Contraseña demasiado larga"}), 400
        if password_actual == password_nuevo:
            return jsonify({"status": "error", "message": "La nueva contraseña debe ser diferente a la actual"}), 400

        try:
            doc = Cliente.find_by_id(cliente_id)
        except Exception:
            return jsonify({"status": "error", "message": "Error de base de datos"}), 500

        if not doc:
            return jsonify({"status": "error", "message": "Cliente no encontrado"}), 404

        if not PasswordService.verify_password(password_actual, doc.get("password", "")):
            return jsonify({"status": "error", "message": "Contraseña actual incorrecta"}), 401

        try:
            new_hash = PasswordService.hash_password(password_nuevo)
            Cliente.update_password(cliente_id, new_hash)
        except Exception as e:
            logger.error("Error cambiando contraseña: %s", e)
            return jsonify({"status": "error", "message": "Error al cambiar la contraseña"}), 500

        return jsonify({"status": "success", "message": "Contraseña actualizada correctamente"}), 200
