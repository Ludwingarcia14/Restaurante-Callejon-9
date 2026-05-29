# Manual Técnico — Sistema de Gestión Restaurante Callejón 9

> **Versión:** 1.0  
> **Fecha:** Abril 2026  
> **Stack:** Python 3.11 · Flask 3.1 · MongoDB · Socket.IO · Scikit-learn · PySpark

---

## Tabla de Contenidos

1. [Descripción General](#1-descripción-general)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Stack Tecnológico](#3-stack-tecnológico)
4. [Requisitos Previos](#4-requisitos-previos)
5. [Instalación y Configuración](#5-instalación-y-configuración)
6. [Variables de Entorno](#6-variables-de-entorno)
7. [Estructura del Proyecto](#7-estructura-del-proyecto)
8. [Modelos de Datos (MongoDB)](#8-modelos-de-datos-mongodb)
9. [Roles y Permisos](#9-roles-y-permisos)
10. [Módulos del Sistema](#10-módulos-del-sistema)
11. [API REST — Referencia de Endpoints](#11-api-rest--referencia-de-endpoints)
12. [Servicios Especiales](#12-servicios-especiales)
13. [Patrón CQRS](#13-patrón-cqrs)
14. [Despliegue en Producción](#14-despliegue-en-producción)
15. [Seguridad](#15-seguridad)
16. [Solución de Problemas Frecuentes](#16-solución-de-problemas-frecuentes)

---

## 1. Descripción General

El **Sistema de Gestión Restaurante Callejón 9** es una plataforma web integral desarrollada en Python/Flask con base de datos MongoDB. Permite administrar de forma unificada las operaciones de un restaurante: atención de mesas, gestión de pedidos en cocina, control de inventario y análisis de ventas.

### Características Principales

- **Gestión en tiempo real** de pedidos y mesas mediante WebSockets (Socket.IO)
- **4 roles diferenciados** con permisos granulares por módulo
- **Autenticación de dos factores (2FA)** vía TOTP (Google Authenticator / Authy)
- **Analytics con MapReduce** sobre MongoDB Aggregation Pipeline
- **Segmentación K-Means** de mesas para análisis de desempeño del mesero
- **Backup y restauración** automática de la base de datos
- **Integración con Mercado Pago** para pagos en línea
- **Sistema de notificaciones** en tiempo real con Socket.IO

---

## 2. Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTE (Browser)                        │
│          HTML/CSS/JS · Tailwind · Chart.js · SweetAlert2        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP / WebSocket
┌──────────────────────────▼──────────────────────────────────────┐
│                    SERVIDOR FLASK (Python 3.11)                  │
│                                                                  │
│  ┌──────────┐  ┌────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │  Routes  │  │Controllers │  │   Services   │  │   CQRS   │  │
│  │ routes.py│→ │ /auth      │  │ /security    │  │/commands │  │
│  │ 250+ ep. │  │ /mesero    │  │ /notif.      │  │/queries  │  │
│  │          │  │ /cocina    │  │ /email       │  │          │  │
│  │          │  │ /inventario│  │ /backups     │  │          │  │
│  │          │  │ /analytics │  │ /data        │  │          │  │
│  └──────────┘  └────────────┘  └──────────────┘  └──────────┘  │
│                                                                  │
│  ┌─────────────────────┐   ┌─────────────────────────────────┐  │
│  │   Flask-SocketIO    │   │         Extensions              │  │
│  │  (async threading)  │   │  socketio · cors · session      │  │
│  └─────────────────────┘   └─────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ PyMongo
┌──────────────────────────▼──────────────────────────────────────┐
│                         MongoDB Atlas                            │
│                                                                  │
│  usuarios · comandas · mesas · platillos · insumos              │
│  movimientos_inventario · ventas · notificaciones · alertas     │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo de una Solicitud HTTP

```
Browser → routes.py → @login_required → @rol_required → Controller → Model → MongoDB → JSON/HTML
```

### Flujo WebSocket (Socket.IO)

```
Cliente → socket.emit('join_room', 'cocina')
Servidor → socketio.emit('nuevo_pedido', data, room='cocina')
Cocina   → SweetAlert2 + sonido + actualización automática
```

---

## 3. Stack Tecnológico

### Backend

| Librería | Versión | Propósito |
|----------|---------|-----------|
| Flask | 3.1.2 | Framework web principal |
| Flask-SocketIO | — | WebSockets en tiempo real |
| Flask-CORS | 6.0.2 | Manejo de CORS |
| Flask-Session | 0.8.0 | Sesiones en filesystem |
| PyMongo | 4.15.5 | Driver MongoDB |
| python-dotenv | 1.2.1 | Variables de entorno |
| scikit-learn | 1.8.0 | K-Means clustering |
| pandas | 2.3.3 | Manipulación de datos |
| numpy | 2.4.0 | Cálculos numéricos |
| PySpark | 3.5.0 | Procesamiento distribuido |
| pyotp | 2.9.0 | TOTP / 2FA |
| qrcode | 8.2 | Generación de QR |
| bcrypt | 5.0.0 | Hash de contraseñas |
| PyJWT | 2.10.1 | JSON Web Tokens |
| fpdf | 1.7.2 | Generación de PDFs |
| gunicorn | 20.1.0 | Servidor WSGI producción |

### Frontend

| Tecnología | Propósito |
|------------|-----------|
| Tailwind CSS (CDN) | Estilos y diseño responsive |
| Chart.js | Gráficas y visualizaciones |
| SweetAlert2 | Alertas y modales |
| Bootstrap Icons | Iconografía |
| Socket.IO Client | Comunicación en tiempo real |
| jQuery 3.7.1 | Utilidades DOM |

### Base de Datos

| Componente | Detalle |
|------------|---------|
| MongoDB Atlas | Base de datos principal en nube |
| Colecciones | 9 colecciones principales |
| Driver | PyMongo 4.15.5 nativo |

---

## 4. Requisitos Previos

### Software Requerido

| Requisito | Versión Mínima | Notas |
|-----------|---------------|-------|
| Python | 3.11+ | Se recomienda 3.11 o 3.13 |
| pip | 23+ | Gestor de paquetes |
| MongoDB | Atlas o 6.0+ local | URI de conexión requerida |
| Git | 2.x | Control de versiones |
| Java JDK | 11+ (opcional) | Requerido solo si se usa PySpark |

### Recursos de Sistema (Desarrollo)

- **RAM:** 2 GB mínimo (4 GB recomendado con PySpark)
- **Disco:** 1 GB espacio libre
- **Red:** Acceso a internet para MongoDB Atlas y CDNs

---

## 5. Instalación y Configuración

### 5.1 Clonar el Repositorio

```bash
git clone https://github.com/Ludwingarcia14/Restaurante-Callejon-9.git
cd Restaurante-Callejon-9
git checkout main
```

### 5.2 Crear Entorno Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 5.3 Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **Nota:** La instalación puede tomar varios minutos debido a PySpark y scikit-learn.

### 5.4 Configurar Variables de Entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar con tus credenciales
nano .env   # o el editor de tu preferencia
```

Ver la sección [Variables de Entorno](#6-variables-de-entorno) para el detalle de cada variable.

### 5.5 Inicializar Datos de Prueba (Opcional)

```bash
# Poblar inventario con datos de muestra
python seed_inventario.py

# Poblar productos/menú
python seed_productos.py
```

### 5.6 Ejecutar la Aplicación

```bash
# Modo desarrollo
python app.py

# La aplicación estará disponible en:
# http://localhost:5000
```

### 5.7 Verificar la Instalación

Abrir en el navegador: `http://localhost:5000/login`

Debe mostrarse la pantalla de inicio de sesión con el logo de Callejón 9.

---

## 6. Variables de Entorno

El archivo `.env` debe contener las siguientes variables:

```env
# ─── Aplicación ───────────────────────────────────────────────────
APP_ENV=development          # development | production
APP_NAME=Callejon9
PORT=5000
TIMEZONE=America/Mexico_City

# ─── Base de Datos ────────────────────────────────────────────────
MONGO_URI=mongodb+srv://USUARIO:PASSWORD@cluster.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=callejon9

# ─── Seguridad Flask ──────────────────────────────────────────────
SECRET_KEY=clave-secreta-aleatoria-larga-aqui
SESSION_COOKIE_SECURE=false     # true en producción con HTTPS
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax

# ─── Autenticación de Dos Factores ────────────────────────────────
EMERGENCY_2FA_KEY=callejon9-emergency-2024

# ─── Notificaciones ───────────────────────────────────────────────
USE_LOCAL_SOCKET=true           # false en producción con servidor Node
NODE_NOTIFICATIONS_URL=http://localhost:8000

# ─── Mercado Pago (opcional) ──────────────────────────────────────
MP_ACCESS_TOKEN=APP_USR-...
MP_PUBLIC_KEY=APP_USR-...
```

### Generación de SECRET_KEY

```python
import secrets
print(secrets.token_hex(32))
```

---

## 7. Estructura del Proyecto

```
Restaurante-Callejon-9/
│
├── app.py                          # Punto de entrada, configuración Flask + SocketIO
├── routes.py                       # Registro de todas las rutas (250+ endpoints)
├── extensions.py                   # Instancia única de SocketIO
├── requirements.txt                # Dependencias Python
├── .env / .env.example             # Variables de entorno
│
├── config/                         # Configuración centralizada
│   ├── db.py                       # Conexión MongoDB (PyMongo)
│   ├── settings.py                 # Constantes y parámetros
│   ├── server.py                   # Servidor HTTPS (producción)
│   ├── spark_config.py             # Sesión Apache Spark
│   └── mongo_spark_conexion.py     # Conector MongoDB ↔ Spark
│
├── models/                         # Modelos de datos y lógica de acceso a BD
│   ├── empleado_model.py           # Usuarios, roles y permisos
│   ├── comanda_model.py            # Comandas y pedidos
│   ├── mesa_model.py               # Estado y asignación de mesas
│   ├── inventario_model.py         # Insumos, movimientos, alertas
│   ├── menu_model.py               # Platillos, categorías, recetas
│   ├── venta_model.py              # Ventas y cortes de caja
│   ├── notificacion.py             # Notificaciones del sistema
│   ├── reports_model.py            # Datos para reportes financieros
│   └── ...
│
├── controllers/                    # Controladores por módulo
│   ├── auth/AuthController.py      # Login, logout, 2FA
│   ├── mesero/
│   │   └── kmeans_controller.py    # K-Means segmentación de mesas
│   ├── cocina/cocinaController.py  # Gestión de pedidos en cocina
│   ├── inventario/                 # Control de insumos y movimientos
│   ├── analytics/                  # KPIs y MapReduce
│   ├── settings/settingsController.py  # Config de cuenta y 2FA
│   ├── mesa/, comanda/, venta/
│   ├── propina/, historial/
│   ├── reports/, support/, pago/
│   └── admin/BackupController.py   # Respaldo y restauración
│
├── services/                       # Servicios de negocio reutilizables
│   ├── security/two_factor_service.py  # TOTP, QR, códigos temporales
│   ├── notificaciones/             # Servicio de notificaciones
│   ├── email/email_service.py      # Envío de correos
│   ├── backups/backups.py          # Lógica de respaldo
│   └── data_service.py
│
├── cqrs/                           # Patrón Command/Query Responsibility Segregation
│   ├── commands/                   # Escrituras (crear, actualizar, eliminar)
│   │   ├── admin/                  # Comandos de administración
│   │   ├── inventario/
│   │   ├── menu/
│   │   └── handlers/
│   └── queries/                    # Lecturas (reportes, dashboards)
│       ├── admin/
│       ├── inventario/
│       └── handlers/
│
├── resources/views/                # Plantillas Jinja2 (61 archivos HTML)
│   ├── layout/                     # Layouts base por rol
│   │   ├── layout_base.html        # Admin
│   │   ├── layout_mesero.html      # Mesero
│   │   ├── layout_cocina.html      # Cocina
│   │   └── layout_inventario.html  # Inventario
│   ├── login.html
│   ├── admin/                      # Vistas del administrador
│   ├── mesero/                     # Vistas del mesero
│   ├── cocina/                     # Vistas de cocina
│   ├── inventario/                 # Vistas de inventario
│   ├── caja/                       # Vistas de caja
│   ├── reports/                    # Reportes generales
│   └── errors/                     # Páginas 401, 404
│
├── static/                         # Archivos estáticos
│   ├── css/main.css
│   ├── js/                         # Scripts JavaScript
│   └── images/                     # Imágenes y logos
│
├── analytics/                      # Scripts MapReduce / PySpark
│   ├── 01_mapreduce.py
│   └── dashboard_mapreduce.py
│
├── flask_session/                  # Almacenamiento de sesiones (filesystem)
├── seed_inventario.py              # Datos de prueba: inventario
└── seed_productos.py               # Datos de prueba: platillos
```

---

## 8. Modelos de Datos (MongoDB)

### 8.1 Colección `usuarios`

```json
{
  "_id": "ObjectId",
  "usuario_email": "string (único)",
  "usuario_clave": "string",
  "usuario_nombre": "string",
  "usuario_apellidos": "string",
  "usuario_rol": "string (1|2|3|4)",
  "usuario_status": "int (0=inactivo, 1=activo)",
  "usuario_tokensession": "string",
  "usuario_foto": "string (URL)",
  "fecha_conexion": "datetime",

  "2fa_enabled": "boolean",
  "2fa_tipo": "string (app|email|sms)",
  "2fa_secret": "string (TOTP Base32)",

  "mesero_numero": "int",
  "mesero_turno": "string",
  "mesas_asignadas": ["int"],
  "mesero_puede_cerrar_cuenta": "boolean",
  "mesero_puede_aplicar_descuento": "boolean",

  "cocina_numero": "int",
  "cocina_puesto": "string",
  "cocina_turno": "string",
  "cocina_area": "string",

  "inventario_numero": "int",
  "inventario_turno": "string",
  "inventario_areas_responsables": ["string"],
  "inventario_puede_registrar_entradas": "boolean",
  "inventario_puede_registrar_salidas": "boolean",
  "inventario_puede_realizar_ajustes": "boolean",
  "inventario_gestiona_proveedores": "boolean",

  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 8.2 Colección `comandas`

```json
{
  "_id": "ObjectId",
  "folio": "string (COM-YYMMDDHHMMSS)",
  "mesa_numero": "int",
  "num_comensales": "int",
  "mesero_id": "ObjectId",
  "mesero_nombre": "string",
  "estado": "string (nueva|enviada|lista|pagada|cerrada)",
  "items": [
    {
      "producto_id": "string",
      "nombre": "string",
      "cantidad": "int",
      "precio": "float",
      "subtotal": "float",
      "estado_cocina": "string (pendiente|en_preparacion|listo|entregado)",
      "fecha_pedido": "datetime"
    }
  ],
  "total": "float",
  "propina": "float",
  "total_final": "float",
  "metodo_pago": "string (efectivo|tarjeta|transferencia|mixto)",
  "fecha_apertura": "datetime",
  "fecha_envio_cocina": "datetime",
  "fecha_cierre": "datetime"
}
```

### 8.3 Colección `mesas`

```json
{
  "_id": "ObjectId",
  "numero": "int (único)",
  "estado": "string (disponible|ocupada|limpieza)",
  "comensales": "int",
  "mesero_id": "ObjectId",
  "cuenta_activa_id": "ObjectId",
  "fecha_ocupacion": "datetime",
  "activa": "boolean"
}
```

### 8.4 Colección `insumos`

```json
{
  "_id": "ObjectId",
  "nombre": "string",
  "categoria": "string (carnes|verduras|lacteos|granos|bebidas|condimentos|desechables|limpieza|otros)",
  "unidad_medida": "string (kg|gr|lt|ml|pza|caja|paquete)",
  "stock_actual": "float",
  "stock_minimo": "float",
  "costo_unitario": "float",
  "proveedor_id": "ObjectId",
  "activo": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 8.5 Colección `movimientos_inventario`

```json
{
  "_id": "ObjectId",
  "insumo_id": "ObjectId",
  "tipo": "string (entrada|salida|ajuste|merma)",
  "cantidad": "float",
  "unidad_medida": "string",
  "costo_unitario": "float",
  "costo_total": "float",
  "proveedor_id": "ObjectId",
  "empleado_id": "ObjectId",
  "razon": "string",
  "referencia": "string",
  "fecha": "datetime",
  "created_at": "datetime"
}
```

### 8.6 Colección `platillos`

```json
{
  "_id": "ObjectId",
  "nombre": "string",
  "descripcion": "string",
  "categoria": "string (entrada|plato_fuerte|bebida|postre|especial)",
  "precio": "float",
  "disponible": "boolean",
  "imagen_url": "string",
  "receta": {
    "insumos": [
      { "insumo_id": "ObjectId", "cantidad": "float", "unidad_medida": "string" }
    ],
    "tiempo_preparacion": "int (minutos)",
    "dificultad": "string (fácil|medio|difícil)"
  },
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 8.7 Colección `ventas`

```json
{
  "_id": "ObjectId",
  "numero_venta": "int (secuencial)",
  "mesa_numero": "int",
  "mesero_id": "ObjectId",
  "mesero_nombre": "string",
  "comensales": "int",
  "platillos": [
    {
      "nombre": "string",
      "cantidad": "int",
      "precio_unitario": "float",
      "subtotal": "float"
    }
  ],
  "subtotal": "float",
  "propina": "float",
  "total": "float",
  "metodo_pago": "string",
  "estado": "string (completada|cancelada)",
  "fecha": "datetime",
  "created_at": "datetime"
}
```

### 8.8 Colección `notificaciones`

```json
{
  "_id": "ObjectId",
  "tipo": "string (LOGIN|LOGOUT|ERROR|PEDIDO|PAGO|ALERTA)",
  "mensaje": "string",
  "id_usuario": "ObjectId",
  "leida": "boolean",
  "fecha": "datetime",
  "created_at": "datetime"
}
```

### 8.9 Colección `alertas_stock`

```json
{
  "_id": "ObjectId",
  "insumo_id": "ObjectId",
  "tipo": "string (stock_critico|stock_bajo)",
  "mensaje": "string",
  "resuelta": "boolean",
  "fecha_alerta": "datetime",
  "fecha_resolucion": "datetime"
}
```

---

## 9. Roles y Permisos

El sistema implementa **RBAC (Role-Based Access Control)** definido en `models/empleado_model.py`.

| ID | Rol | Dashboard | Permisos Principales |
|----|-----|-----------|---------------------|
| `1` | **Administrador** | `/dashboard/admin` | Gestión total: empleados, menú, ventas, inventario, analytics, backup |
| `2` | **Mesero** | `/dashboard/mesero` | Mesas, comandas, cobros, propinas, historial, K-Means |
| `3` | **Cocina** | `/dashboard/cocina` | Ver y actualizar estado de pedidos, consultar inventario |
| `4` | **Inventario** | `/inventario/dashboard` | Insumos, movimientos, alertas, proveedores, reportes |

### Decoradores de Seguridad

```python
# Requiere sesión activa
@login_required

# Requiere rol específico (puede ser uno o varios)
@rol_required(['1'])          # Solo administrador
@rol_required(['1', '2'])     # Admin o Mesero
@rol_required(['3', '4'])     # Cocina o Inventario

# Requiere permiso granular específico
@permiso_required('can_delete')
```

---

## 10. Módulos del Sistema

### 10.1 Autenticación (AuthController)

**Archivo:** `controllers/auth/AuthController.py`

| Método | Descripción |
|--------|-------------|
| `login()` | Valida credenciales, verifica 2FA si está activo |
| `logout()` | Limpia sesión y token en BD |
| `verify_2fa()` | Verifica código OTP y completa el login |
| `_completar_login()` | Puebla sesión Flask tras autenticación exitosa |
| `emergency_disable_2fa()` | Desactiva 2FA por email sin requerir login |

### 10.2 Gestión de Mesas (MesaController)

**Archivo:** `controllers/mesa/mesaController.py`

Gestiona el estado de las mesas mediante el modelo `Mesa`, el cual incluye manejo de tipos mixtos (int/string) para los números de mesa en MongoDB.

### 10.3 Gestión de Comandas (ComandaController)

**Archivo:** `controllers/comanda/comandaController.py`

Maneja el ciclo de vida de una comanda:
`nueva → enviada (a cocina) → lista → pagada/cerrada`

### 10.4 Cocina (CocinaController)

**Archivo:** `controllers/cocina/cocinaController.py`

- Recibe pedidos mediante Socket.IO (`room='cocina'`)
- Calcula tiempo de espera usando `fecha_pedido` de cada ítem
- Emite notificaciones al mesero cuando un pedido está listo

### 10.5 Inventario (InventarioController)

**Archivo:** `controllers/inventario/inventarioController.py`

Incluye el helper `_build_chart_data()` que genera las 4 gráficas de reporte:
- Estado de stock (dona)
- Distribución por categoría (barras)
- Historial de movimientos por día (línea, 4 series)
- Top 5 insumos por valor (barras horizontales)

### 10.6 Analytics (AnalyticsController)

**Archivo:** `controllers/analytics/analytics_controller.py`

Implementa 7 pipelines de agregación MongoDB (equivalente a MapReduce):
- KPIs generales, Top platillos, Ventas por día, Métodos de pago, Horas pico, Rendimiento meseros, Ventas por mesa

### 10.7 K-Means Mesero (MeseroKMeansController)

**Archivo:** `controllers/mesero/kmeans_controller.py`

Segmenta las mesas atendidas por el mesero en 3 clusters usando `scikit-learn`:
- Entrada: `(num_visitas, ticket_promedio)` — últimos 90 días
- Normalización: `StandardScaler`
- Algoritmo: `KMeans(k=3, random_state=42)`
- Clusters: **VIP** · **Regulares** · **Ocasionales**

### 10.8 Configuración y 2FA (SettingsController)

**Archivo:** `controllers/settings/settingsController.py`

- Actualización de perfil de usuario
- Setup de 2FA (genera QR / código email)
- Activación y desactivación de 2FA

### 10.9 Backup y Restauración (BackupController)

**Archivo:** `controllers/admin/BackupController.py`

- Exporta todas las colecciones a un archivo JSON
- Restauración completa desde archivo de respaldo
- Configuración de respaldo automático

---

## 11. API REST — Referencia de Endpoints

### Autenticación

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| `GET/POST` | `/login` | Público | Inicio de sesión |
| `GET` | `/logout` | Todos | Cerrar sesión |
| `POST` | `/verify-2fa` | Público | Verificar código 2FA |
| `GET` | `/api/2fa/emergency-disable` | Público | Desactivar 2FA de emergencia |

### Configuración de Cuenta

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| `GET` | `/settings` | Todos | Página de configuración |
| `POST` | `/api/usuario/actualizar` | Todos | Actualizar perfil |
| `POST` | `/api/2fa/setup` | Todos | Iniciar setup 2FA |
| `POST` | `/api/2fa/verify` | Todos | Verificar y activar 2FA |
| `POST` | `/api/2fa/disable` | Todos | Desactivar 2FA |

### Administrador — Empleados

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| `GET` | `/admin/empleados` | 1 | Lista de empleados |
| `GET/POST` | `/admin/empleados/crear` | 1 | Crear empleado |
| `GET/POST` | `/admin/empleados/editar/<id>` | 1 | Editar empleado |
| `GET` | `/api/empleados/todos` | 1 | API lista empleados |
| `POST` | `/api/empleados/<id>/actualizar` | 1 | Actualizar empleado |
| `POST` | `/api/empleados/<id>/eliminar` | 1 | Eliminar empleado |
| `POST` | `/api/empleados/<id>/desconectar` | 1 | Forzar desconexión |

### Administrador — Menú

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| `GET` | `/admin/menu` | 1 | Lista platillos |
| `GET/POST` | `/admin/menu/crear` | 1 | Crear platillo |
| `GET/POST` | `/admin/menu/editar/<id>` | 1 | Editar platillo |
| `GET` | `/api/menu` | 1,2 | API lista menú |
| `POST` | `/api/menu/<id>/toggle` | 1 | Activar/desactivar platillo |
| `POST` | `/api/menu/<id>/eliminar` | 1 | Eliminar platillo |

### Administrador — Analytics

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| `GET` | `/admin/analytics` | 1 | Vista analytics |
| `GET` | `/api/analytics/kpis` | 1 | KPIs generales |
| `GET` | `/api/analytics/top-platillos` | 1 | Top 10 platillos |
| `GET` | `/api/analytics/ventas-por-dia` | 1 | Ventas últimos 30 días |
| `GET` | `/api/analytics/metodos-pago` | 1 | Distribución de pagos |
| `GET` | `/api/analytics/horas-pico` | 1 | Horas de mayor actividad |
| `GET` | `/api/analytics/rendimiento-meseros` | 1 | Desempeño por mesero |
| `GET` | `/api/analytics/ventas-por-mesa` | 1 | Consumo por mesa |

### Administrador — Backup

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| `GET` | `/admin/backup` | 1 | Vista backup |
| `POST` | `/admin/backup/create` | 1 | Crear respaldo JSON |
| `POST` | `/admin/backup/restore` | 1 | Restaurar base de datos |
| `POST` | `/admin/backup/configure` | 1 | Configurar auto-backup |

### Mesero

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| `GET` | `/dashboard/mesero` | 2 | Dashboard |
| `GET` | `/mesero/mesas` | 2 | Mis mesas |
| `GET` | `/api/mesero/mesas/estado` | 2 | Estado mesas asignadas |
| `GET` | `/mesero/comandas` | 2 | Comandas activas |
| `POST` | `/api/mesero/cuenta/abrir` | 2 | Abrir nueva cuenta |
| `POST` | `/api/mesero/comanda/<id>/items` | 2 | Agregar ítems |
| `POST` | `/api/mesero/cuenta/<id>/cerrar` | 2 | Cerrar y cobrar |
| `GET` | `/mesero/propinas` | 2 | Propinas del día |
| `GET` | `/api/mesero/propinas/hoy` | 2 | API propinas hoy |
| `GET` | `/mesero/historial` | 2 | Historial de cuentas |
| `GET` | `/api/mesero/historial` | 2 | API historial (filtrable por fecha) |
| `GET` | `/mesero/kmeans` | 2 | Segmentación K-Means |
| `GET` | `/api/mesero/kmeans` | 2 | API datos K-Means |
| `GET` | `/api/mesero/estadisticas/dia` | 2 | Estadísticas del día |

### Cocina

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| `GET` | `/dashboard/cocina` | 3 | Dashboard en tiempo real |
| `GET` | `/cocina/pedidos` | 3 | Pedidos pendientes |
| `GET` | `/cocina/en-proceso` | 3 | Pedidos en preparación |
| `GET` | `/cocina/listos` | 3 | Pedidos listos |
| `POST` | `/api/cocina/pedido/iniciar` | 3 | Marcar en preparación |
| `POST` | `/api/cocina/pedido/listo` | 3 | Marcar como listo |
| `POST` | `/api/cocina/pedido/entregado` | 3 | Marcar como entregado |
| `GET` | `/api/cocina/estadisticas` | 3 | Estadísticas (tiempos) |
| `GET` | `/cocina/graficas-inventario` | 3 | Gráficas de inventario |

### Inventario

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| `GET` | `/inventario/dashboard` | 4 | Dashboard |
| `GET` | `/inventario/insumos` | 4 | Lista de insumos |
| `GET/POST` | `/inventario/insumos/crear` | 4 | Crear insumo |
| `GET/POST` | `/inventario/movimientos/entrada` | 4 | Registrar entrada |
| `GET/POST` | `/inventario/movimientos/salida` | 4 | Registrar salida |
| `GET/POST` | `/inventario/movimientos/merma` | 4 | Registrar merma |
| `GET` | `/inventario/movimientos/historial` | 4 | Historial movimientos |
| `GET` | `/inventario/alertas` | 4 | Alertas de stock |
| `POST` | `/api/inventario/alertas/resolver` | 4 | Marcar alerta resuelta |
| `GET/POST` | `/inventario/proveedores/crear` | 4 | Crear proveedor |
| `GET` | `/inventario/reportes` | 3,4 | Reportes con gráficas |

### Notificaciones

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| `GET` | `/api/me` | Todos | Datos de sesión actual |
| `GET` | `/api/notificaciones` | Todos | Todas las notificaciones |
| `GET` | `/api/notificaciones/no-leidas` | Todos | No leídas |
| `GET` | `/api/notificaciones/contador` | Todos | Cantidad no leídas |
| `PUT` | `/api/notificaciones/<id>/leida` | Todos | Marcar como leída |
| `POST` | `/api/notificaciones/marcar-todas-leidas` | Todos | Marcar todas leídas |
| `DELETE` | `/api/notificaciones/<id>` | Todos | Eliminar notificación |

### Pagos (Mercado Pago)

| Método | Ruta | Rol | Descripción |
|--------|------|-----|-------------|
| `POST` | `/api/pago/crear/<cuenta_id>` | 2 | Crear preferencia de pago |
| `GET` | `/pago/exitoso` | Público | Callback pago exitoso |
| `GET` | `/pago/fallido` | Público | Callback pago fallido |
| `POST` | `/api/webhook/mercadopago` | Público | IPN webhook |
| `GET` | `/api/pago/verificar` | 2 | Verificar estado de pago |

---

## 12. Servicios Especiales

### 12.1 Socket.IO — Comunicación en Tiempo Real

**Archivo:** `extensions.py`, `app.py`

```python
# Configuración
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",
    manage_session=False
)

# Eventos del servidor
@socketio.on("connect")
@socketio.on("disconnect")
@socketio.on("join_room")     # Cliente se une a una sala

# Emisión desde controladores
socketio.emit("nuevo_pedido", data, room="cocina")
socketio.emit("pedido_listo", data, room=f"user_{mesero_id}")
```

**Salas (rooms) disponibles:**

| Sala | Destinatario | Eventos |
|------|-------------|---------|
| `cocina` | Personal de cocina | `nuevo_pedido` |
| `user_{id}` | Mesero específico | `pedido_listo` |
| `admin` | Administrador | Notificaciones generales |

### 12.2 Autenticación de Dos Factores (2FA)

**Archivo:** `services/security/two_factor_service.py`

**Flujo completo de activación:**

```
1. Usuario → /settings → Tab "Seguridad"
2. Selecciona tipo: App (TOTP) o Email
3. POST /api/2fa/setup → genera secreto + QR
4. Escanea QR con Google Authenticator / Authy
5. Ingresa código de 6 dígitos para confirmar
6. POST /api/2fa/verify → valida y guarda en BD
7. 2FA activo desde el próximo login
```

**Flujo de login con 2FA activo:**

```
1. Usuario ingresa email + contraseña
2. Sistema valida credenciales
3. Detecta 2fa_enabled=true → guarda pending_login en sesión
4. Frontend muestra modal para ingresar código OTP
5. POST /verify-2fa → verifica TOTP con pyotp
6. Si válido → _completar_login() → redirige al dashboard
```

**Recuperación de emergencia:**

```
GET /api/2fa/emergency-disable?email=usuario@correo.com
```

### 12.3 K-Means — Segmentación de Mesas

**Archivo:** `controllers/mesero/kmeans_controller.py`

```python
# Pipeline de datos
pipeline = [
    {"$match": {"mesero_id": mesero_oid, "estado": {"$in": ["pagada", "cerrada"]},
                "fecha_cierre": {"$gte": hace_90_dias}}},
    {"$group": {
        "_id": "$mesa_numero",
        "num_visitas": {"$sum": 1},
        "ticket_promedio": {"$avg": "$total"},
        "ingreso_total": {"$sum": "$total"}
    }}
]

# Algoritmo
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_raw)
km = KMeans(n_clusters=3, random_state=42, n_init=10)
km.fit(X_scaled)

# Etiquetado automático por score (visitas + ticket)
# Cluster con mayor score → "Mesas VIP"
# Cluster medio         → "Mesas Regulares"
# Cluster menor score   → "Mesas Ocasionales"
```

**Requisito mínimo:** 3 mesas con historial en los últimos 90 días.

### 12.4 Analytics — MapReduce (MongoDB Aggregation Pipeline)

**Archivo:** `controllers/analytics/analytics_controller.py`

Todas las consultas analíticas utilizan el pipeline de agregación de MongoDB, equivalente funcional de MapReduce:

| Operación | Etapas del Pipeline |
|-----------|---------------------|
| Top Platillos | `$match → $unwind → $group → $sort → $limit → $project` |
| Ventas por Día | `$match → $group($dateToString) → $sort → $project` |
| Horas Pico | `$match → $group($hour) → $sort → $project` |
| KPIs | `$match → $group($sum, $avg)` |

---

## 13. Patrón CQRS

El proyecto implementa una separación básica entre comandos (escrituras) y consultas (lecturas) en la carpeta `cqrs/`.

```
cqrs/
├── commands/       # Modifican estado: crear, actualizar, eliminar
│   ├── admin/      # create_admin, update_user, delete_usuario
│   ├── inventario/ # create_insumo, update_stock
│   ├── menu/       # create_platillo, update_platillo
│   └── handlers/   # notificacion_handler
└── queries/        # Solo lectura: dashboards, reportes
    ├── admin/      # dashboard_query, users_query
    ├── inventario/ # stock_query, movimientos_query
    └── handlers/   # query handlers
```

---

## 14. Despliegue en Producción

### 14.1 Con Gunicorn

```bash
# Instalar gunicorn (ya en requirements.txt)
pip install gunicorn

# Ejecutar con workers
gunicorn -w 4 -b 0.0.0.0:5000 --worker-class eventlet app:app
```

### 14.2 Variables de Entorno para Producción

```env
APP_ENV=production
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Strict
MONGO_URI=mongodb+srv://...  # URI de producción
SECRET_KEY=clave-muy-larga-y-aleatoria
USE_LOCAL_SOCKET=false
```

### 14.3 Consideraciones de Producción

- **HTTPS obligatorio:** Configurar certificado SSL (ver `config/server.py`)
- **MongoDB Atlas:** Usar IP Whitelist para restringir acceso
- **Variables de entorno:** Nunca subir `.env` al repositorio (está en `.gitignore`)
- **Flask-Session:** En producción considerar Redis en lugar de filesystem
- **SECRET_KEY:** Generar con `secrets.token_hex(32)` y nunca compartir

### 14.4 Reiniciar y Monitorear

```bash
# Ver logs en tiempo real
tail -f logs/app.log

# Reiniciar servicio (si se usa systemd)
sudo systemctl restart callejon9
```

---

## 15. Seguridad

### Mecanismos Implementados

| Mecanismo | Implementación |
|-----------|---------------|
| Autenticación | Sesiones Flask con token por sesión |
| Autorización | RBAC con decoradores `@login_required` y `@rol_required` |
| 2FA | TOTP (RFC 6238) vía `pyotp` + QR |
| Sesiones | Filesystem con limpieza automática cada 24h |
| CORS | Orígenes permitidos configurados explícitamente |
| XSS | Jinja2 auto-escaping activo |
| CSRF | Tokens de sesión por solicitud |

### Notas de Seguridad

> ⚠️ **Contraseñas:** En la versión actual de desarrollo, las contraseñas se comparan en texto plano. Para producción se recomienda implementar `bcrypt` (ya incluido en `requirements.txt`) en el proceso de login y registro.

---

## 16. Solución de Problemas Frecuentes

### Error: `MongoServerError: bad auth`

```
Causa: Credenciales MongoDB incorrectas o IP no autorizada en Atlas.
Solución: Verificar MONGO_URI en .env y agregar IP en MongoDB Atlas Network Access.
```

### Error: `ModuleNotFoundError: No module named 'flask_socketio'`

```
Causa: Entorno virtual no activado o dependencias no instaladas.
Solución:
  source venv/bin/activate   # Linux/Mac
  venv\Scripts\activate      # Windows
  pip install -r requirements.txt
```

### Error: `RuntimeError: Working outside of application context`

```
Causa: Código que accede a 'db' fuera de una solicitud Flask activa.
Solución: Asegurarse de que los accesos a MongoDB ocurran dentro de funciones
         de controlador llamadas por Flask, no en el nivel de módulo.
```

### Las notificaciones de cocina no llegan en tiempo real

```
Causa: Instancia duplicada de Socket.IO (bug previo).
Solución verificada:
  1. extensions.py crea la instancia única de socketio
  2. app.py importa desde extensions y llama socketio.init_app(app)
  3. app.py usa socketio.run(app) en lugar de app.run()
  4. Todos los controladores importan 'from extensions import socketio'
```

### Error 2FA: `Código incorrecto` aunque el código es correcto

```
Causa: Desincronización de reloj entre servidor y dispositivo autenticador.
Solución: El parámetro valid_window=1 en pyotp.TOTP.verify() permite
          un margen de ±30 segundos. Verificar que el reloj del servidor
          esté sincronizado (NTP).
```

### K-Means devuelve `aviso` en lugar de datos

```
Causa: El mesero tiene menos de 3 mesas con historial en los últimos 90 días.
Solución: Es comportamiento esperado. Se necesitan al menos 3 puntos de datos
          para ejecutar KMeans(k=3). No requiere corrección.
```

---

*Manual Técnico — Restaurante Callejón 9 · Versión 1.0 · Abril 2026*
