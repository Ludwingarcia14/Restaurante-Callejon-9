# Callejón 9 — Sistema Integral de Gestión para Restaurantes

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Flask](https://img.shields.io/badge/backend-Flask-black.svg)
![MongoDB](https://img.shields.io/badge/database-MongoDB-47A248.svg)
![scikit-learn](https://img.shields.io/badge/analytics-scikit--learn-F7931E.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Sistema web para la gestión operativa de un restaurante: comandas, inventario, cocina, pagos y analítica con machine learning (CRISP-DM · K-Means + Random Forest).

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Backend | Flask 3.1 |
| Base de datos | MongoDB Atlas (pymongo) |
| Plantillas | Jinja2 |
| Analítica ML | scikit-learn, NumPy |
| Pagos | MercadoPago |
| Tiempo real | Flask-SocketIO |
| Frontend | TailwindCSS + Chart.js + Bootstrap Icons |

---

## Requisitos previos

- Python 3.11
- Cuenta en [MongoDB Atlas](https://www.mongodb.com/atlas) (o instancia local)
- Git

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Ludwingarcia14/Restaurante-Callejon-9.git
cd Restaurante-Callejon-9
```

### 2. Crear y activar entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
# MongoDB
MONGO_URI=mongodb+srv://<usuario>:<password>@<cluster>.mongodb.net/callejon9?retryWrites=true&w=majority
MONGO_DB_NAME=callejon9

# Flask
SECRET_KEY=tu_clave_secreta
PORT=5000

# MercadoPago (opcional)
MP_ACCESS_TOKEN=tu_access_token
MP_PUBLIC_KEY=tu_public_key
```

### 5. Ejecutar la aplicación

```bash
python app.py
```

La app queda disponible en `http://localhost:5000`.

---

## Datos de prueba (seed)

Para poblar la base de datos con comandas de prueba y validar la analítica:

```bash
# Insertar 2000 registros
python scripts/seed_data.py

# Especificar cantidad
python scripts/seed_data.py --n 500

# Limpiar datos anteriores y reinsertar
python scripts/seed_data.py --limpiar
```

El script genera comandas distribuidas en 3 clusters:

| Cluster | Mesas | Ticket promedio |
|---|---|---|
| VIP | 1–2 | ~$400–480 MXN |
| Regular | 3–5 | ~$150–165 MXN (alta frecuencia) |
| Ocasional | 6–8 | ~$140–160 MXN (baja frecuencia) |

> Requiere que existan meseros con `usuario_rol: "2"` y platillos disponibles en la base de datos.

---

## Roles del sistema

| Rol | Acceso |
|---|---|
| `1` — Administrador | Dashboard, menú, ventas, reportes, analytics |
| `2` — Mesero | Comandas, menú, propinas, historial, segmentación ML |
| `3` — Cocina | Cola de pedidos en tiempo real |
| `4` — Inventario | Control de insumos y stock |

---

## Analítica CRISP-DM (rol Mesero)

El módulo de machine learning implementa las 6 fases de CRISP-DM sobre las comandas de los últimos 90 días:

| Página | Ruta | Descripción |
|---|---|---|
| Segmentación | `/mesero/kmeans` | K-Means k=3, scatter plot, recomendaciones |
| Random Forest | `/mesero/arbol` | 200 árboles, importancia de features, OOB score |
| Diagnóstico | `/mesero/diagnostico` | Estadísticas por mesa, métodos de pago |
| Metodología | `/mesero/metodologia` | Documentación completa de las 6 fases |

Ver `METODOLOGIA_CRISP_DM.md` para la explicación técnica detallada con fragmentos de código.

---

## Estructura del proyecto

```
├── app.py                             # Punto de entrada Flask
├── config/
│   └── db.py                          # Conexión MongoDB
├── controllers/
│   ├── admin/                         # Controladores administrador
│   ├── mesero/                        # kmeans, randomforest, diagnostico, metodologia
│   ├── auth/                          # Autenticación y roles
│   └── ...
├── services/
│   ├── mesero_kmeans_service.py       # K-Means clustering
│   ├── mesero_randomforest_service.py # Random Forest
│   ├── mesero_diagnostico_service.py  # Diagnóstico estadístico
│   └── ...
├── routes/
│   ├── mesero_routes.py
│   ├── admin_routes.py
│   └── ...
├── resources/views/                   # Plantillas Jinja2
├── static/                            # CSS, JS, imágenes
├── scripts/
│   └── seed_data.py                   # Generador de datos de prueba
├── requirements.txt
├── .env.example
└── METODOLOGIA_CRISP_DM.md            # Documentación técnica ML
```

---

## Equipo

| Nombre | Rol |
|---|---|
| Ludwin Garcia Gaytan | Arquitectura y coordinación |
| Octavio Duarte Villavicencio | Developer |
| Valeria Mercado Serrano | Developer |
| Regina Ibarra Alba | Developer |

---

## Licencia

MIT — consulta el archivo `LICENSE` para más detalles.
