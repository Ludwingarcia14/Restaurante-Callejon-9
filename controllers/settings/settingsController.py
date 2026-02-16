from flask import session, redirect, url_for, render_template, request, jsonify
from models.empleado_model import Usuario
from services.security.two_factor_service import TwoFactorService
from config.db import db
from bson import ObjectId
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)


class SettingsController:
    """Controlador para gestion de configuracion de cuenta (2FA, perfil, seguridad)"""

    @staticmethod
    def settings():
        """Renderiza la pagina de configuracion segun el rol del usuario"""
        if "usuario_id" not in session:
            return redirect(url_for('routes.login'))

        user_id = session["usuario_id"]
        user = Usuario.find_by_id(user_id)

        if not user:
            return "Usuario no encontrado", 404

        # Determinar template segun rol
        template_map = {
            "1": "admin/config/config.html",
            "2": "mesero/config/config.html",
            "3": "cocina/config/config.html",
            "4": "inventario/config/config.html",
        }

        template = template_map.get(str(session.get("usuario_rol")), "admin/config/config.html")

        return render_template(
            template,
            is_2fa_active=user.get('2fa_enabled', False)
        )

    # ==========================================
    # API: DATOS DE USUARIO
    # ==========================================

    @staticmethod
    def get_telefono():
        """Obtiene el telefono del usuario"""
        if "usuario_id" not in session:
            return jsonify({'status': 'error', 'message': 'No autorizado'}), 401

        try:
            user = Usuario.find_by_id(session["usuario_id"])
            return jsonify({
                'status': 'success',
                'telefono': user.get('telefono', '') if user else ''
            })
        except Exception as e:
            logging.error(f"Error al obtener telefono: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @staticmethod
    def actualizar_perfil():
        """Actualiza el perfil del usuario"""
        if "usuario_id" not in session:
            return jsonify({'status': 'error', 'message': 'No autorizado'}), 401

        data = request.json or {}
        user_id = session["usuario_id"]

        update_data = {}

        if 'nombre' in data:
            update_data['usuario_nombre'] = data['nombre']
        if 'apellidos' in data:
            update_data['usuario_apellidos'] = data['apellidos']
        if 'telefono' in data:
            update_data['telefono'] = data['telefono']

        if not update_data:
            return jsonify({'status': 'error', 'message': 'No hay datos para actualizar'}), 400

        try:
            result = Usuario.update(user_id, update_data)

            if result.modified_count == 1:
                if 'usuario_nombre' in update_data:
                    session['usuario_nombre'] = update_data['usuario_nombre']
                if 'usuario_apellidos' in update_data:
                    session['usuario_apellidos'] = update_data['usuario_apellidos']

                logging.info(f"Perfil actualizado: {user_id}")
                return jsonify({'status': 'success', 'message': 'Perfil actualizado correctamente'})
            else:
                return jsonify({'status': 'error', 'message': 'No se pudo actualizar'}), 500
        except Exception as e:
            logging.error(f"Error al actualizar perfil: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    # ==========================================
    # API: 2FA
    # ==========================================

    @staticmethod
    def generate_2fa_setup():
        """Genera configuracion 2FA (QR para app, codigo para email/sms)"""
        if "usuario_id" not in session:
            return jsonify({'status': 'error', 'message': 'No autorizado'}), 401

        user_id = session["usuario_id"]
        user = Usuario.find_by_id(user_id)

        if not user:
            return jsonify({'status': 'error', 'message': 'Usuario no encontrado'}), 404

        tipo = request.json.get('tipo', 'app')

        if tipo == 'app':
            secret_key = TwoFactorService.generar_secret()
            username = user.get('usuario_email')

            if not username:
                return jsonify({'status': 'error', 'message': 'Email no disponible.'}), 400

            qr_base64 = TwoFactorService.generar_qr_code(secret_key, username)

            session['temp_2fa_secret'] = secret_key
            session['temp_2fa_tipo'] = 'app'

            return jsonify({
                'status': 'success',
                'secret_key': secret_key,
                'qr_image': qr_base64,
                'tipo': 'app'
            })

        elif tipo == 'email':
            email_destino = user.get('usuario_email')
            if not email_destino:
                return jsonify({'status': 'error', 'message': 'Email no disponible.'}), 400

            email_code = TwoFactorService.generar_codigo_sms()

            session['temp_2fa_secret'] = email_code
            session['temp_2fa_tipo'] = 'email'
            session['temp_2fa_email'] = email_destino

            logging.info(f"Codigo 2FA por email: {email_code} -> {email_destino}")

            return jsonify({
                'status': 'success',
                'message': f'Codigo enviado a {email_destino}.',
                'tipo': 'email'
            })

        return jsonify({'status': 'error', 'message': 'Tipo no valido'}), 400

    @staticmethod
    def verify_and_enable_2fa():
        """Verifica el codigo 2FA y activa la proteccion"""
        if "usuario_id" not in session:
            return jsonify({'status': 'error', 'message': 'Sesion no valida'}), 401

        user_id = session["usuario_id"]
        data = request.json or {}

        otp_code = data.get('otp_code') or data.get('code')
        secret_key = session.get('temp_2fa_secret')
        tipo = session.get('temp_2fa_tipo')

        if not secret_key or not otp_code or not tipo:
            return jsonify({'status': 'error', 'message': 'Datos faltantes'}), 400

        is_valid = False
        secret_to_save = None

        if tipo == 'app':
            is_valid = TwoFactorService.verificar_totp(secret_key, otp_code)
            if is_valid:
                secret_to_save = secret_key

        elif tipo == 'email':
            is_valid = (str(otp_code) == str(secret_key))

        if not is_valid:
            return jsonify({'status': 'error', 'message': 'Codigo invalido'}), 401

        result = Usuario.update_2fa_status(
            user_id=user_id,
            is_enabled=True,
            tipo=tipo,
            secret=secret_to_save,
            telefono=None
        )

        session.pop('temp_2fa_secret', None)
        session.pop('temp_2fa_tipo', None)
        session.pop('temp_2fa_email', None)

        session['2fa_enabled'] = True
        session['2fa_tipo'] = tipo
        session['2fa_secret'] = secret_to_save

        if result and result.modified_count == 1:
            logging.info(f"2FA activado para usuario: {user_id}")
            return jsonify({'status': 'success', 'message': '2FA activado correctamente'})
        else:
            return jsonify({'status': 'error', 'message': 'Error al guardar en BD'}), 500

    @staticmethod
    def disable_2fa():
        """Desactiva la autenticacion de dos factores"""
        if "usuario_id" not in session:
            return jsonify({'status': 'error', 'message': 'No autorizado'}), 401

        user_id = session["usuario_id"]

        result = Usuario.update_2fa_status(
            user_id=user_id,
            is_enabled=False,
            tipo=None,
            secret=None,
            telefono=None
        )

        session['2fa_enabled'] = False
        session['2fa_tipo'] = None
        session['2fa_secret'] = None

        if result and result.modified_count == 1:
            logging.info(f"2FA desactivado para usuario: {user_id}")
            return jsonify({'status': 'success', 'message': '2FA desactivado'})
        else:
            return jsonify({'status': 'error', 'message': 'Error al desactivar'}), 500
