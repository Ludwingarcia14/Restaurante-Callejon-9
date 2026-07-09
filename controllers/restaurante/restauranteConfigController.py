"""
Controlador de Configuracion del Restaurante (tenant).

Lee y guarda los ajustes del negocio (identidad, tema, fiscal, contacto) en el
documento del tenant activo. Solo admin (lo garantizan los decoradores de ruta).
"""
import os
import logging
from flask import jsonify, request
from werkzeug.utils import secure_filename

from utils.tenant_context import require_current_tenant
from models.restaurante_model import Restaurante
from services.restaurante.restaurante_service import build_config_update

logger = logging.getLogger(__name__)

_LOGO_EXTS = {"png", "jpg", "jpeg", "webp", "svg"}
_UPLOAD_DIR = os.path.join("static", "uploads")


class RestauranteConfigController:

    @staticmethod
    def get_config():
        """Devuelve la configuracion actual del restaurante para poblar el formulario."""
        doc = Restaurante.find_by_id(require_current_tenant()) or {}
        fiscal = doc.get("fiscal", {}) or {}
        iva = fiscal.get("iva")
        return jsonify({
            "nombre": doc.get("nombre", ""),
            "logo": doc.get("logo", ""),
            "tema": doc.get("tema", {}) or {},
            "fiscal": {
                # se expone como porcentaje para el formulario
                "iva": round(iva * 100, 2) if isinstance(iva, (int, float)) else "",
                "moneda": fiscal.get("moneda", ""),
            },
            "contacto": doc.get("contacto", {}) or {},
        })

    @staticmethod
    def save_config():
        """Guarda los campos editables de la configuracion del restaurante."""
        data = request.get_json(silent=True) or {}
        update = build_config_update(data)
        if update:
            Restaurante.update_config(require_current_tenant(), update)
        return jsonify({"success": True})

    @staticmethod
    def upload_logo():
        """Sube el logo del restaurante y guarda su ruta en el tenant."""
        tenant_id = require_current_tenant()
        archivo = request.files.get("logo")
        if not archivo or not archivo.filename:
            return jsonify({"success": False, "message": "No se recibió archivo"}), 400

        ext = archivo.filename.rsplit(".", 1)[-1].lower() if "." in archivo.filename else ""
        if ext not in _LOGO_EXTS:
            return jsonify({"success": False, "message": "Formato no permitido (usa PNG/JPG/WEBP/SVG)"}), 400

        try:
            os.makedirs(_UPLOAD_DIR, exist_ok=True)
            nombre_archivo = secure_filename(f"logo_{tenant_id}.{ext}")
            ruta = os.path.join(_UPLOAD_DIR, nombre_archivo)
            archivo.save(ruta)
            ruta_publica = "/" + ruta.replace("\\", "/")
            Restaurante.update_config(tenant_id, {"logo": ruta_publica})
            return jsonify({"success": True, "logo": ruta_publica})
        except Exception as e:
            logger.error("Error subiendo logo: %s", e)
            return jsonify({"success": False, "message": "Error al subir el logo"}), 500
