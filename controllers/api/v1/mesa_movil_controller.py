"""
Endpoints de mesa para la app móvil.
El escaneo de QR no requiere auth — el cliente puede ver la mesa antes de loguearse.
"""
import logging
import qrcode
import io

from flask import request, jsonify, send_file
from models.mesa_model import Mesa

logger = logging.getLogger(__name__)


class MesaMovilController:

    @staticmethod
    def escanear_qr(codigo_qr: str):
        """
        GET /api/v1/mesas/escanear/<codigo_qr>
        Valida el QR y devuelve info de la mesa. Sin auth.
        """
        if not codigo_qr or len(codigo_qr) > 64:
            return jsonify({"status": "error", "message": "Código QR inválido"}), 400

        mesa_doc = Mesa.find_by_qr(codigo_qr)
        if not mesa_doc:
            return jsonify({"status": "error", "message": "Mesa no encontrada. Verifica el código QR"}), 404

        estado = str(mesa_doc.get("estado", "disponible")).lower()

        return jsonify({
            "status": "success",
            "mesa": {
                "numero": mesa_doc.get("numero"),
                "capacidad": mesa_doc.get("capacidad", 0),
                "estado": estado,
                "seccion": mesa_doc.get("seccion", ""),
                "tipo": mesa_doc.get("tipo", "interior"),
                "disponible_para_pedir": estado in ("disponible", "ocupada"),
            },
        }), 200

    @staticmethod
    def generar_imagen_qr(numero: str):
        """
        GET /api/v1/admin/mesas/<numero>/qr
        Devuelve imagen PNG del QR para imprimir. Requiere auth de admin (manejado en routes).
        """
        codigo = Mesa.get_or_create_qr(numero)
        if not codigo:
            return jsonify({"status": "error", "message": "Mesa no encontrada"}), 404

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(codigo)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        return send_file(
            buf,
            mimetype="image/png",
            as_attachment=True,
            download_name=f"qr_mesa_{numero}.png",
        )

    @staticmethod
    def listar_qr_mesas():
        """
        GET /api/v1/admin/mesas/qr-tokens
        Devuelve los tokens QR de todas las mesas para configurar el panel de QRs.
        """
        # Genera QR para las que no tengan
        nuevas = Mesa.generar_qr_todas()

        mesas = Mesa.find_all()
        resultado = [
            {
                "numero": m.get("numero"),
                "codigo_qr": m.get("codigo_qr", ""),
                "estado": m.get("estado", "disponible"),
            }
            for m in mesas
        ]

        return jsonify({
            "status": "success",
            "mesas": resultado,
            "nuevas_generadas": nuevas,
        }), 200
