# Librerías del Proyecto — Restaurante Callejón 9

Todas las dependencias están definidas en `requirements.txt`. A continuación se explica cada una, agrupada por su función dentro del sistema.

---

## Framework web

### Flask `3.1.2`
El núcleo de la aplicación. Maneja las rutas HTTP, sesiones, renderizado de plantillas y el ciclo de vida de cada petición. Todo el sistema corre sobre Flask.

### Werkzeug `3.1.4`
Librería base que Flask usa internamente para manejar peticiones y respuestas HTTP, enrutamiento y utilidades de seguridad como el hashing de contraseñas.

### Jinja2 `3.1.6`
Motor de plantillas usado para generar el HTML de todas las vistas. Permite usar variables, condicionales y bucles dentro de los archivos `.html` con la sintaxis `{{ }}` y `{% %}`.

### MarkupSafe `3.0.3`
Dependencia de Jinja2. Escapa automáticamente caracteres peligrosos en el HTML para prevenir ataques XSS.

### itsdangerous `2.2.0`
Utilidad de Flask para firmar y verificar datos de forma segura, principalmente usada para proteger las cookies de sesión.

### click `8.3.1`
Utilidad de línea de comandos que Flask usa internamente para su CLI (`flask run`, `flask shell`, etc.).

### blinker `1.9.0`
Sistema de señales que Flask usa para eventos internos como `before_request` y `teardown_appcontext`.

---

## Extensiones Flask

### flask-cors `6.0.2`
Habilita los encabezados CORS (Cross-Origin Resource Sharing) en las rutas de la API. Permite que el frontend haga peticiones a la API desde distintos orígenes o puertos.

### Flask-Session `0.8.0`
Extiende el sistema de sesiones de Flask para almacenarlas en el servidor (en memoria o archivo) en lugar de en una cookie del cliente. Necesario para manejar sesiones de usuario entre peticiones.

### Flask-SocketIO `5.6.1`
Integra WebSockets en Flask mediante el protocolo Socket.IO. Usado para las notificaciones en tiempo real a cocina cuando entra una nueva comanda.

### python-socketio `>=5.0.0`
Implementación del protocolo Socket.IO del lado del servidor. Flask-SocketIO lo usa internamente.

### python-engineio `>=4.0.0`
Capa de transporte por debajo de Socket.IO. Maneja la conexión WebSocket real entre cliente y servidor.

---

## Base de datos

### pymongo `4.15.5`
Driver oficial de MongoDB para Python. Todas las operaciones con la base de datos (consultas, inserciones, agregaciones, actualizaciones) se hacen a través de esta librería.

### dnspython `2.8.0`
Permite a pymongo resolver las URLs de conexión en formato `mongodb+srv://` que usa MongoDB Atlas. Sin esta librería la conexión a Atlas no funciona.

---

## Machine Learning y Analítica

### scikit-learn `1.8.0`
Librería central del módulo CRISP-DM. Usada para:
- `KMeans` — segmentación de mesas en clusters (VIP, Regular, Ocasional)
- `StandardScaler` — normalización de features antes del clustering
- `RandomForestClassifier` — entrenamiento del bosque de 200 árboles sobre los labels de K-Means
- `silhouette_score` — evaluación de la calidad de los clusters
- `export_text` — exportación del árbol representativo como texto legible

### numpy `2.4.0`
Operaciones matemáticas sobre matrices. Usado para construir las matrices de features `X_kmeans` y `X_arbol`, calcular la desviación estándar de importancias entre árboles y reordenar los clusters por centroide.

### scipy `1.16.3`
Dependencia de scikit-learn. Provee algoritmos matemáticos de bajo nivel usados internamente por K-Means y Random Forest.

### joblib `1.5.3`
Dependencia de scikit-learn. Paraleliza el entrenamiento de los 200 árboles del Random Forest usando múltiples núcleos del procesador.

### threadpoolctl `3.6.0`
Controla el número de hilos usados por las operaciones numéricas de numpy y scipy. Dependencia de scikit-learn.

### pandas `2.3.3`
Manipulación de datos en formato tabular. Usado en el módulo de analytics del administrador para procesar y transformar datos de ventas antes de generar reportes.

### python-dateutil `2.9.0.post0`
Extensión del módulo `datetime` de Python. Facilita el parseo y manipulación de fechas con formatos complejos.

### pytz `2025.2`
Manejo de zonas horarias. Usado para convertir fechas a la zona horaria `America/Mexico_City` definida en `.env`.

### tzdata `2025.3`
Base de datos de zonas horarias. Requerida por pytz en sistemas donde no está instalada a nivel de OS (principalmente Windows).

### six `1.17.0`
Utilidad de compatibilidad Python 2/3. Dependencia transitiva de algunas librerías como python-dateutil.

---

## Seguridad y Autenticación

### bcrypt `5.0.0`
Hasheo seguro de contraseñas. Cuando un usuario se registra o cambia su contraseña, bcrypt genera un hash con sal aleatoria que se almacena en MongoDB.

### PyJWT `2.10.1`
Generación y verificación de tokens JWT (JSON Web Tokens). Usado para autenticar peticiones a la API y en los tokens de sesión de Socket.IO.

### cryptography `46.0.3`
Primitivas criptográficas de bajo nivel. Dependencia de PyJWT y otras librerías de seguridad del proyecto.

### pyotp `2.9.0`
Implementa autenticación de dos factores (2FA) mediante códigos TOTP (Time-based One-Time Password), compatible con Google Authenticator.

### qrcode `8.2`
Genera los códigos QR que el usuario escanea para configurar el 2FA en su app de autenticación.

### pillow `10.4.0`
Procesamiento de imágenes. Dependencia de qrcode para renderizar el código QR como imagen PNG.

---

## Pagos

### mercadopago `2.3.0`
SDK oficial de MercadoPago. Permite crear preferencias de pago, procesar pagos con tarjeta y recibir webhooks de confirmación de pago dentro del flujo de cierre de comanda.

---

## HTTP y Red

### requests `2.32.5`
Cliente HTTP de Python. Usado para hacer llamadas a APIs externas, incluyendo las notificaciones y webhooks de MercadoPago.

### urllib3 `2.6.2`
Librería HTTP de bajo nivel usada por requests internamente.

### certifi `2025.11.12`
Bundle de certificados SSL/TLS. Garantiza que las conexiones HTTPS a MongoDB Atlas y MercadoPago sean seguras y verificadas.

### charset-normalizer `3.4.4`
Detecta y normaliza la codificación de caracteres en respuestas HTTP. Dependencia de requests.

### idna `3.11`
Manejo de nombres de dominio internacionales (IDN). Dependencia de requests para resolver URLs.

---

## Configuración

### python-dotenv `1.2.1`
Lee el archivo `.env` y carga las variables de entorno en `os.environ` al iniciar la aplicación. Permite separar la configuración del código fuente.

### cachelib `0.13.0`
Backend de caché usado por Flask-Session para almacenar las sesiones de usuario en el sistema de archivos del servidor.

---

## Generación de documentos

### fpdf `1.7.2`
Genera documentos PDF. Usado en el módulo de reportes del administrador para exportar resúmenes de ventas, comandas o inventario en formato PDF.

---

## Producción

### gunicorn `20.1.0`
Servidor WSGI de producción para Python. En producción (Render, Railway, etc.) reemplaza al servidor de desarrollo de Flask y maneja múltiples workers en paralelo. Definido en el `Procfile`.

### schedule `>=1.2.0`
Permite programar tareas periódicas en Python (equivalente a un cron job). Usado para tareas de mantenimiento automático como limpieza de sesiones o generación de reportes programados.
