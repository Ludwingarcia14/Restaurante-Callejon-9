import http.server
import ssl
import socketserver

# --- Configuración ---
PUERTO = 8443  # Puedes usar 443, pero 8443 no requiere permisos de admin
CERT_FILE = 'localhost+2.pem'
KEY_FILE = 'localhost+2-key.pem'
# ---------------------

# Configura el manejador de archivos (el mismo que http.server)
handler = http.server.SimpleHTTPRequestHandler

# Crea el contexto SSL
contexto_ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
contexto_ssl.load_cert_chain(CERT_FILE, KEY_FILE)

# Inicia el servidor
with socketserver.TCPServer(("", PUERTO), handler) as httpd:
    # Envuelve el socket del servidor con el contexto SSL
    httpd.socket = contexto_ssl.wrap_socket(httpd.socket, server_side=True)
    
    print(f"¡Servidor HTTPS iniciado en https://127.0.0.1:{PUERTO}")
    print("Presiona Ctrl+C para detener.")
    
    # Sirve para siempre
    httpd.serve_forever()