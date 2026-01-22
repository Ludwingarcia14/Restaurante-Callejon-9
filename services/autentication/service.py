import pyotp
import qrcode
import base64
import io
import random
import string

class TwoFactorService:
    """
    Clase de servicio que encapsula toda la lógica de Autenticación de Dos Factores (2FA),
    incluyendo la generación de claves secretas, URIs de provisioning, QR, 
    y la verificación de códigos OTP (TOTP).
    """
    
    # Nombre de la aplicación que se mostrará en Google Authenticator
    ISSUER_NAME = "GestorPyme" 

    @staticmethod
    def generate_secret_key():
        """Genera una nueva clave secreta base32 aleatoria compatible con TOTP."""
        return pyotp.random_base32()

    @staticmethod
    def get_provisioning_uri(username, secret_key):
        """
        Crea la URI de aprovisionamiento para el escaneo del QR.
        Ejemplo: otplib://totp/user@app.com?secret=SECRET&issuer=App
        """
        return pyotp.totp.TOTP(secret_key).provisioning_uri(
            name=username,
            issuer_name=TwoFactorService.ISSUER_NAME
        )

    @staticmethod
    def generate_qr_code(provisioning_uri):
        """
        Genera el código QR para el URI de aprovisionamiento y lo devuelve en formato base64.
        """
        # Crear la imagen QR
        img = qrcode.make(provisioning_uri)
        
        # Usar un buffer en memoria para guardar la imagen (evitar archivos temporales)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        
        # Devolver la imagen codificada en base64
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    @staticmethod
    def verify_code(secret_key, otp_code):
        """
        Verifica si el código OTP proporcionado es válido para la clave secreta dada.
        Retorna True si es válido, False en caso contrario.
        """
        try:
            totp = pyotp.TOTP(secret_key)
            # Verifica el código con una ventana de tiempo (tolerancia)
            return totp.verify(otp_code)
        except Exception as e:
            # Manejar cualquier excepción durante la verificación (ej. clave secreta inválida)
            print(f"Error durante la verificación TOTP: {e}")
            return False

    @staticmethod
    def generate_email_code(length=6):
        """
        Genera un código numérico aleatorio para simular la verificación por SMS o Email.
        Este código es temporal y DEBE guardarse en sesión o caché para su verificación.
        """
        return ''.join(random.choices(string.digits, k=length))

    # --- Método adicional para verificación de códigos SMS/Email (temporal) ---
    # NOTA: La lógica de verificación real (comparar código temporal con el código introducido)
    # se encuentra en el controlador, ya que requiere acceder a la 'session'.