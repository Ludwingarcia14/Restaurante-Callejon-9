# controllers/api/cqrs/commands/services/recaptcha_service.py

import requests
import os
import logging

class RecaptchaService:
    """Clase para encapsular la comunicación con la API de reCAPTCHA."""
    
    # Las claves secretas se leen del entorno
    SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
    MIN_SCORE = 0.5

    @classmethod
    def verify(cls, recaptcha_response, remote_addr, errors_list):
        """Verifica la respuesta de reCAPTCHA y añade errores a la lista si falla."""
        if not recaptcha_response:
            errors_list.append("Por favor completa la verificación de seguridad")
            return False

        payload = {
            "secret": cls.SECRET_KEY,
            "response": recaptcha_response,
            "remoteip": remote_addr
        }
        try:
            response = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload, timeout=5)
            response.raise_for_status() 
            result = response.json()
            success = result.get("success", False)
            score = result.get("score", 0)

            if not success or score < cls.MIN_SCORE:
                errors_list.append(f"No se pasó la verificación de seguridad (Score: {score:.2f})")
                return False
            return True
        except Exception:
            errors_list.append("Error interno al verificar la seguridad")
            return False