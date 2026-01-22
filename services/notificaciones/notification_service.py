import requests
import json

def notificar_usuario(user_id, evento, mensaje, datos_extra=None):
    #NODE_URL = "http://localhost:3000/api/notificar"
    NODE_URL = "https://pyme-notificaciones.onrender.com/api/notificar"


    if datos_extra is None: 
        datos_extra = {}

    # CORRECCIÓN 2: Quitar "room". El target es solo el ID convertido a string.
    payload = {
        "target": str(user_id), 
        "evento": evento,
        "data": {"mensaje": mensaje, **datos_extra}
    }

    try:
        response = requests.post(NODE_URL, json=payload, timeout=5)

        if response.status_code == 200:
            resp_json = response.json()
            # Verificamos si Node dijo "Enviado" o "Usuario no conectado"
            if resp_json.get("status") == "Enviado":
                print(f"✅Notificación push enviada al usuario {user_id}")
                return True
            else:
                print(f"⚠️Node recibió la petición pero el usuario {user_id} no estaba conectado.")
                return False
        else:
            print(f"❌Node respondió error {response.status_code}: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌Error de conexión con servidor de notificaciones: {e}")
        return False

def notificar_financiera(email_destino, datos_cliente, financiera_nombre):
    if not email_destino or email_destino == "null":
        print(f"⚠️Sin email para {financiera_nombre}")
        return

    asunto = f"Nuevo Prospecto Calificado para {financiera_nombre}"
    # Aquí iría tu lógica real de envío de correo (SendGrid, Nodemailer, SMTP, etc.)
    print(f"📧[EMAIL SIMULADO] Para: {email_destino} | Asunto: {asunto}")
    return True
