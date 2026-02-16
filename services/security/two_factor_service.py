"""
Servicio de Two-Factor Authentication (2FA)
============================================
Implementa verificación TOTP usando pyotp

Tipos de 2FA:
    - "app": TOTP con aplicaciones como Google Authenticator
    - "sms": Código por SMS
    - "email": Código por email
"""

import pyotp
import qrcode
import io
import base64
import secrets
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

# Constantes
CODIGO_2FA_LENGTH = 6
CODIGO_EXPIRATION_MINUTES = 5


class TwoFactorService:
    """Servicio auxiliar para operaciones de 2FA"""
    
    # Almacenamiento temporal de códigos (en producción usar Redis)
    _codigos_temporales = {}
    
    @staticmethod
    def generar_secret():
        """Genera un secreto único para TOTP"""
        return pyotp.random_base32()
    
    @staticmethod
    def generar_qr_code(secret, nombre_cuenta, emisor="Callejon 9"):
        """
        Genera un código QR para escanear con la app autenticadora
        
        Args:
            secret: Secreto TOTP
            nombre_cuenta: Email o nombre del usuario
            emisor: Nombre del servicio/empresa
            
        Returns:
            Data URL del código QR (base64)
        """
        # Generar URI compatible con Google Authenticator
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=nombre_cuenta,
            issuer_name=emisor
        )
        
        # Generar código QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a base64
        buffer = io.BytesIO()
        img.save(buffer)
        buffer.seek(0)
        
        data_url = f"data:image/png;base64,{base64.b64encode(buffer.read()).decode()}"
        return data_url
    
    @staticmethod
    def verificar_totp(secret, codigo):
        """
        Verifica un código TOTP usando pyotp
        
        Args:
            secret: Secreto TOTP del usuario
            codigo: Código de 6 dígitos ingreado
            
        Returns:
            True si el código es válido, False en caso contrario
        """
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(codigo, valid_window=1)
        except Exception as e:
            logging.error(f"Error verificando TOTP: {e}")
            return False
    
    @staticmethod
    def generar_codigo_sms():
        """Genera un código numérico de 6 dígitos para SMS/Email"""
        return ''.join(str(secrets.randbelow(10)) for _ in range(CODIGO_2FA_LENGTH))
    
    @staticmethod
    def guardar_codigo_temporal(user_id, codigo):
        """Guarda un código temporal para SMS/Email"""
        TwoFactorService._codigos_temporales[user_id] = {
            "codigo": codigo,
            "expira": datetime.utcnow()
        }
    
    @staticmethod
    def verificar_codigo_temporal(user_id, codigo_ingresado):
        """
        Verifica un código temporal (SMS/Email)
        
        Returns:
            True si el código es válido y no ha expirado
        """
        datos = TwoFactorService._codigos_temporales.get(user_id)
        if not datos:
            return False
        
        # Verificar código
        if datos["codigo"] != codigo_ingresado:
            return False
        
        # Verificar expiración (5 minutos)
        tiempo_transcurrido = (datetime.utcnow() - datos["expira"]).total_seconds()
        if tiempo_transcurrido > CODIGO_EXPIRATION_MINUTES * 60:
            del TwoFactorService._codigos_temporales[user_id]
            return False
        
        # Limpiar código usado
        del TwoFactorService._codigos_temporales[user_id]
        return True
    
    @staticmethod
    def prep_2fa_session(usuario_doc):
        """
        Prepara la sesión con datos de 2FA
        
        Args:
            usuario_doc: Documento del usuario
            
        Returns:
            Dict con datos de 2FA para la sesión
        """
        return {
            "2fa_tipo": usuario_doc.get("2fa_tipo"),
            "2fa_secret": usuario_doc.get("2fa_secret"),
            "2fa_enabled": usuario_doc.get("2fa_enabled", False),
            "2fa_telefono": usuario_doc.get("2fa_telefono"),
            "2fa_email": usuario_doc.get("2fa_email")
        }
