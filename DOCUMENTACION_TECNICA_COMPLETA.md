# 🍽️ Documentación Técnica Completa - Sistema Restaurante Callejón 9

## 📋 Tabla de Contenidos

1. [Visión General del Sistema](#1-visión-general-del-sistema)
2. [Arquitectura del Proyecto](#2-arquitectura-del-proyecto)
3. [Sistema de Autenticación y Seguridad](#3-sistema-de-autenticación-y-seguridad)
4. [Sistema de Roles y Permisos (RBAC)](#4-sistema-de-roles-y-permisos-rbac)
5. [Autenticación de Dos Factores (2FA)](#5-autenticación-de-dos-factores-2fa)
6. [Sistema de Notificaciones](#6-sistema-de-notificaciones)
7. [Sistema de Backup y Recuperación de Datos](#7-sistema-de-backup-y-recuperación-de-datos)
8. [Módulo de Reportes](#8-módulo-de-reportes)
9. [Módulo de Inventario](#9-módulo-de-inventario)
10. [Dashboard y Métricas](#10-dashboard-y-métricas)
11. [API Reference](#11-api-reference)
12. [Configuración y Variables de Entorno](#12-configuración-y-variables-de-entorno)

---

## 1. Visión General del Sistema

### 1.1 Descripción del Proyecto

**Callejón 9** es un sistema integral de gestión para restaurantes desarrollado en Python con Flask. Proporciona una plataforma modular que abarca desde la toma de pedidos hasta el análisis de datos mediante Apache Spark.

### 1.2 Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| **Lenguaje** | Python 3.11 |
| **Framework Backend** | Flask |
| **Base de Datos** | MongoDB (MongoDB Atlas) |
| **Motor de Analítica** | Apache Spark |
| **Frontend** | HTML5, JavaScript (Templates Jinja2) |
| **Autenticación** | JWT + Sesiones Flask |
| **2FA** | TOTP (Google Authenticator) + Códigos Email/SMS |
| **Sesiones** | Flask-Session con almacenamiento filesystem |

### 1.3 Estructura del Proyecto

```
Restaurante-Callejon-9/
├── app.py                    # Punto de entrada principal
├── routes.py                 # Definición de rutas principales
├── config/
│   ├── db.py                # Configuración de MongoDB
│   ├── settings.py           # Configuración de Spark
│   └── server.py            # Configuración del servidor
├── controllers/
│   ├── auth/                # Controlador de autenticación
│   ├── admin/               # Controlador de administración/backup
│   ├── dashboard/           # Controladores de dashboard
│   ├── inventario/          # Controlador de inventario
│   ├── notificaciones/      # Controlador de notificaciones
│   ├── reports/             # Controlador de reportes
│   └── settings/            # Controlador de configuración
├── models/
│   ├── empleado_model.py    # Modelo de usuarios
│   ├── notificacion.py      # Modelo de notificaciones
│   ├── reports_model.py     # Modelo de reportes
│   └── inventario_model.py   # Modelo de inventario
├── cqrs/                    # Patrón CQRS
│   ├── commands/           # Comandos
│   └── queries/             # Consultas
├── services/
│   ├── backups/            # Servicio de backups
│   ├── security/           # Seguridad (2FA)
│   └── notificaciones/     # Servicio de notificaciones
└── resources/views/         # Templates HTML
```

---

## 2. Arquitectura del Proyecto

### 2.1 Flujo de Datos

```
Usuario → Flask Routes → Controllers → Models → MongoDB
                ↓
         CQRS Pattern
                ↓
    Commands/Queries Handlers
```

### 2.2 Patrón de Diseño CQRS

El sistema implementa el patrón **CQRS (Command Query Responsibility Segregation)** para separar las operaciones de lectura y escritura:

#### **Consultas (Queries)** - [`cqrs/queries/`](cqrs/queries/)
- [`notificacion_query_handler.py`](cqrs/queries/handlers/notificacion_query_handler.py): Maneja consultas de notificaciones
- [`usuario_handler.py`](cqrs/queries/handlers/usuario_handler.py): Maneja consultas de usuarios

#### **Comandos (Commands)** - [`cqrs/commands/`](cqrs/commands/)
- [`notificacion_handler.py`](cqrs/commands/handlers/notificacion_handler.py): Maneja comandos de notificaciones
- [`create_admin_command.py`](cqrs/commands/admin/create_admin_command.py): Crea administradores

### 2.3 Configuración de Base de Datos

**Archivo:** [`config/db.py`](config/db.py)

```python
# Conexión a MongoDB Atlas
MONGO_URI = os.getenv("MONGO_URI")  # mongodb+srv://...
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")  # callejon9_prueba

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
```

### 2.4 Inicialización de la Aplicación

**Archivo:** [`app.py`](app.py)

```python
# Configuración de Flask
app = Flask(__name__, template_folder="resources/views", static_folder="static")

# Configuración de CORS
CORS(app, resources={r"/*": {"origins": lista_origenes}}, supports_credentials=True)

# Configuración de Sesiones
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_COOKIE_NAME"] = "callejon9_session"

# Registro de Blueprints
app.register_blueprint(routes_bp)
```

---

## 3. Sistema de Autenticación y Seguridad

### 3.1 Flujo de Login

**Archivo:** [`controllers/auth/AuthController.py`](controllers/auth/AuthController.py)

```python
class AuthController:
    @staticmethod
    def login():
        # 1. Recibe email y password
        # 2. Busca usuario en MongoDB
        # 3. Verifica estado de 2FA
        # 4. Crea sesión si no hay 2FA
        # 5. Solicita verificación 2FA si está habilitado
```

### 3.2 Decoradores de Seguridad

El sistema usa tres niveles de protección:

```python
# 1. Verifica que el usuario esté logueado
@login_required

# 2. Verifica que el usuario tenga el rol correcto
@rol_required(['1', '2', '3', '4'])

# 3. Verifica permisos específicos
@permiso_required('puede_crear')
```

### 3.3 Gestión de Sesiones

**Almacenamiento:** Sistema de archivos (`flask_session/`)
**Duración:** Permanente hasta logout
**Datos almacenados:**
- `usuario_id`: ID del usuario
- `usuario_nombre`: Nombre completo
- `usuario_email`: Correo electrónico
- `usuario_rol`: Rol del usuario (1-4)
- `token_session`: Token de seguridad
- `2fa_enabled`: Estado de 2FA
- `permisos`: Lista de permisos activos

---

## 4. Sistema de Roles y Permisos (RBAC)

### 4.1 Roles Definidos

| Rol ID | Nombre | Descripción |
|--------|--------|-------------|
| `1` | Administrador | Acceso total al sistema |
| `2` | Mesero | Gestión de comandas y mesas |
| `3` | Cocina | Gestión de pedidos en cocina |
| `4` | Inventario | Gestión de insumos y stock |

### 4.2 Matriz de Permisos

**Archivo:** [`models/empleado_model.py`](models/empleado_model.py:167)

```python
class RolPermisos:
    PERMISOS = {
        "1": {
            "nombre": "Administrador",
            "modulos": ["dashboard", "menu", "inventario", "ventas", "reportes", "empleados", "configuracion"],
            "puede_crear": True,
            "puede_editar": True,
            "puede_eliminar": True,
            "puede_ver_reportes": True,
            "acceso_finanzas": True,
            "autoriza_descuentos": True
        },
        "2": {
            "nombre": "Mesero",
            "modulos": ["dashboard", "comandas", "mesas", "clientes"],
            "puede_cerrar_cuenta": True,
            "gestiona_propinas": True
        },
        "3": {
            "nombre": "Cocina",
            "modulos": ["dashboard", "comandas", "inventario_consulta"],
            "ver_comandas_activas": True
        },
        "4": {
            "nombre": "Encargado de Inventario",
            "modulos": ["dashboard", "inventario", "proveedores", "reportes_inventario"],
            "registra_entradas": True,
            "registra_salidas": True,
            "recibe_alertas_stock": True
        }
    }
```

### 4.3 Dashboards por Rol

Cada rol tiene un dashboard específico:

- **Admin:** [`/dashboard/admin`](controllers/dashboard/dashboard_controller.py:48)
- **Mesero:** [`/dashboard/mesero`](controllers/dashboard/dashboard_controller.py:67)
- **Cocina:** [`/dashboard/cocina`](controllers/dashboard/dashboard_controller.py:90)
- **Inventario:** [`/dashboard/inventario`](controllers/dashboard/dashboard_controller.py:112)

---

## 5. Autenticación de Dos Factores (2FA)

### 5.1 Tipos de 2FA Soportados

| Tipo | Descripción | Uso |
|------|-------------|-----|
| `app` | TOTP con Google Authenticator | Genera códigos temporales de 6 dígitos |
| `email` | Código por email | Envía código al correo registrado |
| `sms` | Código por SMS | Envía código al teléfono (pendiente implementación) |

### 5.2 Configuración de 2FA

**Archivo:** [`services/security/two_factor_service.py`](services/security/two_factor_service.py)

#### Generación de Secret TOTP
```python
@staticmethod
def generar_secret():
    """Genera un secreto único para TOTP usando pyotp"""
    return pyotp.random_base32()
```

#### Generación de QR Code
```python
@staticmethod
def generar_qr_code(secret, nombre_cuenta, emisor="Callejon 9"):
    """Genera un código QR compatible con Google Authenticator"""
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=nombre_cuenta,
        issuer_name=emisor
    )
    # Convierte a base64 para mostrar en frontend
```

#### Verificación TOTP
```python
@staticmethod
def verificar_totp(secret, codigo):
    """Verifica código TOTP con ventana de validez de 1 período"""
    totp = pyotp.TOTP(secret)
    return totp.verify(codigo, valid_window=1)
```

### 5.3 Flujo de Activación 2FA

**Archivo:** [`controllers/settings/settingsController.py`](controllers/settings/settingsController.py:105)

```python
# 1. Generar configuración (QR o código)
POST /api/2fa/setup
{
    "tipo": "app" | "email"
}

# 2. Verificar código y activar
POST /api/2fa/verify
{
    "otp_code": "123456"
}

# 3. Desactivar 2FA
POST /api/2fa/disable
```

### 5.4 Recuperación de Emergencia 2FA

**Endpoint:** [`/api/2fa/emergency-disable`](controllers/auth/AuthController.py:370)

```python
@staticmethod
def emergency_disable_2fa(email):
    """
    Deshabilita 2FA para usuarios bloqueados
    Requiere clave de emergencia en variable de entorno: EMERGENCY_2FA_KEY
    """
    # Verifica clave de emergencia
    # Actualiza estado de 2FA en MongoDB a FALSE
```

**Uso:**
```
GET /api/2fa/emergency-disable?email=usuario@email.com&key=callejon9-emergency-2024
```

---

## 6. Sistema de Notificaciones

### 6.1 Arquitectura de Notificaciones

**Archivo:** [`controllers/notificaciones/notificacion_controller.py`](controllers/notificaciones/notificacion_controller.py)

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│  API REST        │────▶│   MongoDB       │
│   (Socket.IO)   │◀────│  Controllers     │◀────│  (notificaciones │
└─────────────────┘     └──────────────────┘      └─────────────────┘)
```

### 6.2 Tipos de Notificaciones por Rol

**Archivo:** [`cqrs/commands/handlers/notificacion_handler.py`](cqrs/commands/handlers/notificacion_handler.py:156)

| Tipo | Admin | Mesero | Cocina | Inventario |
|------|-------|--------|--------|------------|
| LOGIN | ✅ | ✅ | ✅ | ✅ |
| LOGOUT | ✅ | ✅ | ✅ | ✅ |
| PEDIDO_NUEVO | ❌ | ❌ | ✅ | ❌ |
| PEDIDO_LISTO | ❌ | ✅ | ❌ | ❌ |
| STOCK_BAJO | ✅ | ❌ | ❌ | ✅ |
| BACKUP_CREADO | ✅ | ❌ | ❌ | ❌ |
| ERROR_SISTEMA | ✅ | ❌ | ❌ | ❌ |

### 6.3 API de Notificaciones

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/notificaciones` | GET | Obtiene todas las notificaciones |
| `/api/notificaciones/no-leidas` | GET | Obtiene solo no leídas |
| `/api/notificaciones/contador` | GET | Contador de no leídas |
| `/api/notificaciones/<id>/leida` | PUT | Marcar como leída |
| `/api/notificaciones/marcar-todas-leidas` | POST | Marcar todas como leídas |
| `/api/notificaciones/<id>` | DELETE | Eliminar notificación |

### 6.4 Notificaciones del Sistema

**Archivo:** [`controllers/notificaciones/notificacion_controller.py`](controllers/notificaciones/notificacion_controller.py:235)

```python
class NotificacionSistemaController:
    @staticmethod
    def notificar_login(usuario_id, nombre_usuario, rol):
        # Notifica a administradores cuando alguien inicia sesión
        pass

    @staticmethod
    def notificar_backup_creado(usuario_id, nombre_archivo):
        # Notifica creación de backup
        pass

    @staticmethod
    def notificar_error(usuario_id, tipo_error, descripcion):
        # Notifica errores del sistema
        pass

    @staticmethod
    def notificar_movimiento_inventario(usuario_id, tipo_movimiento, nombre_insumo, cantidad):
        # Notifica entradas/salidas de inventario
        pass
```

### 6.5 Zona Horaria

Todas las notificaciones usan **zona horaria de México**:

```python
Mexico_TZ = timezone('America/Mexico_City')

def get_mexico_datetime():
    """Obtiene la fecha y hora actual en zona horaria de Mexico"""
    return datetime.now(Mexico_TZ)
```

---

## 7. Sistema de Backup y Recuperación de Datos

### 7.1 Respaldo Manual

**Archivo:** [`controllers/admin/BackupController.py`](controllers/admin/BackupController.py)

**Endpoint:** `POST /admin/backup/create`

**Parámetros del formulario:**
| Parámetro | Descripción | Valores |
|------------|-------------|---------|
| `collections` | Colecciones a respaldar | Multiple selección |
| `time_range` | Rango temporal | `all`, `24h`, `7d`, `30d` |
| `format` | Formato de archivo | `json`, `zip` |
| `backup_name` | Nombre personalizado | Opcional |

**Colecciones respaldables:**
```
- usuarios
- clientes
- mesas
- comandas
- ventas
- platillos
- actividad_reciente
- estadisticas_diarias
- prestamos
- pagos
- configuracion
- auditoria
- ia_logs
- notificaciones
```

### 7.2 Backup Automático

**Configuración:** [`/admin/backup/configure`](controllers/admin/BackupController.py:286)

**Parámetros JSON:**
```json
{
    "enabled": true,
    "frequency": "daily" | "weekly" | "monthly",
    "hour": "02:00",
    "retention_days": 30
}
```

**Frecuencias disponibles:**
- `daily`: Todos los días a la hora especificada
- `weekly`: Todos los lunes a la hora especificada
- `monthly`: Cada 30 días a la hora especificada

### 7.3 Restauración de Datos

**Endpoint:** `POST /admin/backup/restore`

**Orígenes soportados:**
1. **Archivo del servidor:** Seleccionar de lista existente
2. **Archivo subido:** Subir archivo local (.json o .zip)

**Proceso de restauración:**
```python
def restore():
    # 1. Leer archivo (JSON directo o extraer de ZIP)
    # 2. Convertir JSON a objetos BSON (ObjectIds, Dates)
    # 3. Por cada colección:
    #    - db[col_name].drop()  # Limpiar colección actual
    #    - db[col_name].insert_many(bson_docs)  # Insertar datos
    # 4. Notificar restauración completada
```

### 7.4 Limpieza de Backups Antiguos

El sistema elimina automáticamente respaldos antiguos según la política de retención:

```python
@staticmethod
def _limpiar_respaldos_antiguos():
    """Elimina respaldos antiguos según la retención configurada"""
    # Solo elimina archivos que empiezan con 'auto_backup_'
    # Calcula diferencia de días vs retention_days
    # Elimina archivos más antiguos que el límite
```

### 7.5 Notificaciones de Backup

El sistema envía notificaciones automáticas cuando:
- si Backup creado exitosamente
- no Error durante backup
- en proceso Restauración completada

---

## 8. Módulo de Reportes

### 8.1 Reportes Financieros

**Archivo:** [`models/reports_model.py`](models/reports_model.py)

| Métrica | Método | Descripción |
|---------|--------|-------------|
| Ventas por período | `ventas_por_periodo()` | Agrupado por día/semana/mes |
| Utilidad bruta | `utilidad_bruta()` | Ventas - Costo de insumos |
| Margen por producto | `margen_por_producto()` | Ganancia por platillo |
| Ingresos vs Gastos | `ingresos_vs_gastos()` | Comparación financiera |
| Flujo de caja | `flujo_caja()` | Entradas - Salidas diarias |

### 8.2 Reportes de Inventario

| Métrica | Método | Descripción |
|---------|--------|-------------|
| Consumo por período | `consumo_por_periodo()` | Salidas de insumos |
| Merma acumulada | `merma_acumulada()` | Pérdidas por insumo |
| Rotación inventario | `rotacion_inventario()` | Velocidad de rotación |
| Insumos costosos | `insumos_mas_costosos()` | Top 10 por costo |
| Stock actual | `stock_actual()` | Inventario disponible |

### 8.3 Reportes Operativos

| Métrica | Método | Descripción |
|---------|--------|-------------|
| Rendimiento empleado | `rendimiento_empleado()` | Ventas por mesero |
| Tiempo de servicio | `tiempo_promedio_servicio()` | Minutos por pedido |
| Platillos más vendidos | `platillos_mas_vendidos()` | Top 10 populares |
| Platillos menos rentables | `platillos_menos_rentables()` | Margen bajo |
| Métodos de pago | `distribucion_metodos_pago()` | Efectivo vs Tarjeta |

### 8.4 Exportación de Reportes

**Endpoints disponibles:**

| Formato | Endpoint | Descripción |
|---------|----------|-------------|
| CSV | `/reportes/exportar/csv?reporte=ventas` | Exporta a CSV |
| Excel | `/reportes/exportar/excel?reporte=ventas` | Exporta a Excel (HTML compat) |
| PDF | `/reportes/exportar/pdf?reporte=ventas` | Genera PDF imprimible |

**Parámetros:**
- `reporte`: Tipo de reporte (ventas, inventario, platillos, empleados)
- `fecha_inicio`: Fecha inicial (YYYY-MM-DD)
- `fecha_fin`: Fecha final (YYYY-MM-DD)

### 8.5 Resumen Ejecutivo

**Endpoint:** `/reportes/resumen-ejecutivo`

Genera un dashboard consolidado con:
- Total de ventas
- Utilidad bruta
- Platillo más vendido
- Empleado con mejor rendimiento
- Tendencia de ingresos

---

## 9. Módulo de Inventario

### 9.1 Gestión de Insumos

**Archivo:** [`controllers/inventario/inventarioController.py`](controllers/inventario/inventarioController.py)

| Operación | Endpoint | Rol |
|-----------|----------|-----|
| Listar insumos | `GET /inventario/insumos` | 1, 4 |
| Crear insumo | `POST /inventario/insumos/crear` | 1, 4 |

**Categorías de insumos:**
```python
class CategoriaInsumo(Enum):
    VERDURAS = "verduras"
    FRUTAS = "frutas"
    CARNES = "carnes"
    MARISCOS = "mariscos"
    LACTEOS = "lacteos"
    GRANO = "granos"
    ESPECIAS = "especias"
    BEBIDAS = "bebidas"
    OTROS = "otros"
```

### 9.2 Movimientos de Inventario

| Tipo | Descripción | Efecto en Stock |
|------|-------------|------------------|
| **ENTRADA** | Compra, devolución | ➕ Aumenta |
| **SALIDA** | Uso en cocina, producción | ➖ Disminuye |
| **MERMA** | Caducidad, daño, pérdida | ➖ Disminuye |

### 9.3 Estados de Stock

| Estado | Condición | Color Visual |
|--------|-----------|--------------|
| **Normal** | stock > stock_minimo * 1.5 | Verde |
| **Bajo** | stock_minimo < stock <= stock_minimo * 1.5 | Amarillo |
| **Crítico** | 0 < stock <= stock_minimo | Naranja |
| **Agotado** | stock == 0 | Rojo |

### 9.4 Alertas de Stock

El sistema genera alertas automáticas cuando:
- Stock alcanza nivel crítico
- Insumo está agotado
- Se requiere reorder

**Endpoints de alertas:**
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/inventario/alertas` | GET | Lista alertas activas |
| `/api/inventario/alertas/resolver` | POST | Marca alerta como resuelta |

### 9.5 Historial de Movimientos

**Endpoint:** `GET /inventario/movimientos/historial`

**Filtros disponibles:**
- `insumo_id`: Filtrar por insumo específico
- `tipo`: Tipo de movimiento (entrada, salida, merma)
- `fecha_desde`: Fecha inicial
- `fecha_hasta`: Fecha final

---

## 10. Dashboard y Métricas

### 10.1 Dashboard Admin

**Endpoint:** `GET /dashboard/admin`

**KPIs mostrados:**
- Total empleados por rol
- Mesas ocupadas
- Comandas activas
- Ventas del día
- Cuentas abiertas
- Platillos disponibles

### 10.2 API de Estadísticas

**Archivo:** [`controllers/dashboard/dashboardApiController.py`](controllers/dashboard/dashboardApiController.py)

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/dashboard/admin/stats` | Estadísticas generales |
| `GET /api/dashboard/admin/actividad` | Actividad reciente |
| `GET /api/dashboard/admin/personal` | Personal activo |
| `GET /api/empleados/todos` | Lista completa de empleados |

### 10.3 Personalización por Rol

| Rol | Datos en Sesión | Dashboard |
|-----|-----------------|-----------|
| 1 (Admin) | Permisos completos | `admin/dashboard.html` |
| 2 (Mesero) | Mesas asignadas, propinas | `mesero/dashboard.html` |
| 3 (Cocina) | Área, especialidad | `cocina/dashboard.html` |
| 4 (Inventario) | Áreas responsables | `inventario/dashboard.html` |

---

## 11. API Reference

### 11.1 Autenticación

| Endpoint | Método | Descripción | Auth |
|----------|--------|-------------|------|
| `/login` | POST | Iniciar sesión | No |
| `/logout` | GET | Cerrar sesión | Sí |
| `/verify-2fa` | POST | Verificar 2FA | No* |
| `/api/me` | GET | Datos del usuario | Sí |

### 11.2 Notificaciones

| Endpoint | Método | Descripción | Auth |
|----------|--------|-------------|------|
| `/api/notificaciones` | GET | Lista notificaciones | Sí |
| `/api/notificaciones/no-leidas` | GET | No leídas | Sí |
| `/api/notificaciones/contador` | GET | Contador | Sí |
| `/api/notificaciones/<id>/leida` | PUT | Marcar leída | Sí |
| `/api/notificaciones/marcar-todas-leidas` | POST | Marcar todas | Sí |
| `/api/notificaciones/<id>` | DELETE | Eliminar | Sí |

### 11.3 Configuración (2FA)

| Endpoint | Método | Descripción | Auth |
|----------|--------|-------------|------|
| `/api/2fa/setup` | POST | Generar QR/código | Sí |
| `/api/2fa/verify` | POST | Verificar código | Sí |
| `/api/2fa/disable` | POST | Desactivar 2FA | Sí |
| `/api/2fa/emergency-disable` | GET | Desactivar emergencia | No |

### 11.4 Backup

| Endpoint | Método | Descripción | Rol |
|----------|--------|-------------|-----|
| `/admin/backup` | GET | Panel de backup | 1 |
| `/admin/backup/create` | POST | Crear backup | 1 |
| `/admin/backup/delete/<filename>` | GET | Eliminar archivo | 1 |
| `/admin/backup/restore` | POST | Restaurar | 1 |
| `/admin/backup/configure` | POST | Configurar auto-backup | 1 |

### 11.5 Reportes

| Endpoint | Método | Descripción | Rol |
|----------|--------|-------------|-----|
| `/reportes/financieros` | GET | Reportes financieros | 1 |
| `/reportes/inventario` | GET | Reportes inventario | 1, 4 |
| `/reportes/operativos` | GET | Reportes operativos | 1 |
| `/reportes/api/*` | GET | APIs de reportes | 1 |

### 11.6 Inventario

| Endpoint | Método | Descripción | Rol |
|----------|--------|-------------|-----|
| `/inventario/dashboard` | GET | Dashboard inventario | 1, 4 |
| `/inventario/insumos` | GET | Lista insumos | 1, 4 |
| `/inventario/insumos/crear` | POST | Crear insumo | 1, 4 |
| `/inventario/movimientos/entrada` | POST | Registrar entrada | 1, 4 |
| `/inventario/movimientos/salida` | POST | Registrar salida | 1, 4 |
| `/inventario/movimientos/merma` | POST | Registrar merma | 1, 4 |
| `/inventario/alertas` | GET | Ver alertas | 1, 4 |

---

## 12. Configuración y Variables de Entorno

### 12.1 Archivo .env

**Ubicación:** [`.env`](.env)

```bash
# === CONFIGURACIÓN GENERAL ===
APP_ENV=development
APP_NAME="Callejon9"
PORT=8000
DEBUG=true
TIMEZONE=America/Mexico_City

# === MONGODB ===
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/callejon9_prueba
MONGO_DB_NAME=callejon9_prueba

# === SEGURIDAD ===
SECRET_KEY=clave_ultrasecreta_callejon9_123
JWT_SECRET=jwt_key_para_callejon9
JWT_EXPIRES_IN=3600
JWT_ALGORITHM=HS256

# === CORS ===
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# === SOCKET.IO ===
JWT_SECRET_KEY=callejon9_super_secreto_jwt_2026

# === EMERGENCIA 2FA ===
EMERGENCY_2FA_KEY=callejon9-emergency-2024
```

### 12.2 Colecciones de MongoDB

| Colección | Descripción | Campos clave |
|-----------|-------------|--------------|
| `usuarios` | Empleados del sistema | usuario_email, usuario_clave, usuario_rol, 2fa_* |
| `notificaciones` | Notificaciones del sistema | tipo, mensaje, id_usuario, leida, fecha |
| `insumos` | Productos de inventario | nombre, categoria, stock_actual, stock_minimo |
| `movimientos_inventario` | Historial de movimientos | tipo, insumo_id, cantidad, fecha |
| `ventas` | Transacciones de venta | total, items, fecha, estado |
| `comandas` | Pedidos de clientes | mesa_id, items, estado, mesero_id |
| `mesas` | Mesas del restaurante | numero, capacidad, estado |
| `configuracion` | Configuración del sistema | tipo, enabled, frequency, hour |
| `actividad_reciente` | Log de actividades | accion, usuario_id, timestamp |

### 12.3 Manejo de Errores

El sistema implementa un manejo de errores consistente:

```python
# Formato de respuesta de error
{
    "status": "error",
    "message": "Descripción del error",
    "error": "Detalles técnicos (solo en desarrollo)"
}

# Códigos HTTP
400 - Bad Request (datos inválidos)
401 - Unauthorized (no autenticado)
403 - Forbidden (sin permisos)
404 - Not Found (recurso no existe)
500 - Internal Server Error (error del servidor)
```

---

## 🛠️ Puntos Clave del Código

### A. Sistema de 2FA con TOTP

**Archivo:** [`services/security/two_factor_service.py:34`](services/security/two_factor_service.py:34)

```python
def generar_qr_code(secret, nombre_cuenta, emisor="Callejon 9"):
    """Genera URI compatible con Google Authenticator"""
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=nombre_cuenta,
        issuer_name=emisor
    )
```

**Explicación:** Genera una URI estándar de TOTP que las apps de autenticación pueden escanear. La URI sigue el formato `otpauth://totp/Issuer:Account?secret=XXX&issuer=YYY`.

### B. Recuperación de Emergencia 2FA

**Archivo:** [`controllers/auth/AuthController.py:370`](controllers/auth/AuthController.py:370)

```python
@staticmethod
def emergency_disable_2fa(email):
    """Deshabilita 2FA usando clave de emergencia"""
    emergency_key = os.environ.get('EMERGENCY_2FA_KEY', 'callejon9-emergency-2024')
    provided_key = request.args.get('key', '')
    
    if provided_key != emergency_key:
        return jsonify({"status": "error", "message": "Clave de emergencia incorrecta"}), 403
    
    # Actualiza estado en MongoDB
    Usuario.update_2fa_status(
        user_id=user_id,
        is_enabled=False,
        tipo=None,
        secret=None,
        telefono=None
    )
```

**Explicación:** Permite recuperar cuentas cuando el usuario pierde acceso a su app autenticadora. Requiere clave maestra almacenada en variable de entorno.

### C. Backup con Filtro de Tiempo

**Archivo:** [`controllers/admin/BackupController.py:117`](controllers/admin/BackupController.py:117)

```python
# Filtro por rango de tiempo
if time_range != 'all':
    days = 1 if time_range == '24h' else 7 if time_range == '7d' else 30
    limit_date = datetime.utcnow() - timedelta(days=days)
    date_filter = {"created_at": {"$gte": limit_date}}
```

**Explicación:** Permite crear backups parciales filtrando por fecha. Útil para respaldos incrementales.

### D. Restauración con Conversión BSON

**Archivo:** [`controllers/admin/BackupController.py:269`](controllers/admin/BackupController.py:269)

```python
# Convertir JSON a objetos BSON (ObjectIds, Dates)
bson_docs = json_util.loads(json.dumps(documents))
db[col_name].drop()  # Limpia la colección actual
db[col_name].insert_many(bson_docs)
```

**Explicación:** MongoDB no almacena JSON nativo. Usamos `json_util` de `bson` para convertir tipos especiales como ObjectId y fechas entre JSON y BSON.

### E. Patrón CQRS en Notificaciones

**Archivo:** [`cqrs/commands/handlers/notificacion_handler.py:26`](cqrs/commands/handlers/notificacion_handler.py:26)

```python
@staticmethod
def crear_notificacion(tipo, mensaje, id_usuario, datos_extra=None):
    """Crea notificación en BD y envía push en tiempo real"""
    # 1. Crear notificación en BD
    nueva_notif = {...}
    result = Notificacion.create(nueva_notif)
    
    # 2. Enviar notificación push en tiempo real
    notificar_usuario(
        user_id=id_usuario,
        evento=tipo,
        mensaje=mensaje,
        datos_extra=datos_extra
    )
```

**Explicación:** Separa la lógica de escritura (BD) de la notificación en tiempo real, permitiendo escalar independientemente.

### F. Alertas Automáticas de Inventario

**Archivo:** [`controllers/inventario/inventarioController.py:204`](controllers/inventario/inventarioController.py:204)

```python
# Registrar movimiento
resultado = MovimientoInventario.registrar_movimiento(movimiento_data)

if resultado["success"]:
    # Generar alertas automáticas
    AlertaStock.generar_alertas_automaticas()
```

**Explicación:** Cada vez que se modifica el inventario, el sistema verifica automáticamente si hay stock bajo y genera alertas.

### G. Permisos por Rol

**Archivo:** [`models/empleado_model.py:221`](models/empleado_model.py:221)

```python
@classmethod
def tiene_permiso(cls, rol, permiso):
    permisos_rol = cls.get_permisos(str(rol))
    return permisos_rol.get(permiso, False)
```

**Explicación:** Sistema flexible para verificar permisos específicos. Permite agregar nuevos permisos sin modificar decoradores.

---

## 📊 Métricas del Sistema

### Rendimiento de Ventas

| Métrica | Descripción | Frecuencia |
|---------|-------------|------------|
| Total ventas | Suma de todas las transacciones | Tiempo real |
| Promedio ticket | Ventas / # pedidos | Tiempo real |
| Platillo más vendido | Top 1 por cantidad | Por período |
| Utilidad bruta | Ventas - Costos | Por período |

### Rendimiento de Empleados

| Métrica | Descripción | Rol |
|---------|-------------|-----|
| Ventas por mesero | Total de ventas asignadas | 1, 2 |
| Propinas acumuladas | Total de propinas del día | 1, 2 |
| Tiempo de servicio | Minutos promedio por pedido | 1, 3 |

### Inventario

| Métrica | Descripción | Frecuencia |
|---------|-------------|------------|
| Valor total inventario | stock * costo_unitario | Tiempo real |
| Items críticos | Insumos bajo stock mínimo | Tiempo real |
| Rotación | Costo consumido / Inventario promedio | Por período |

---

## 🔒 Consideraciones de Seguridad

### 1. Almacenamiento de Contraseñas
⚠️ **Nota:** Las contraseñas se almacenan en texto plano. En producción se usara bcrypt:
```python
from werkzeug.security import generate_password_hash, check_password_hash
hash = generate_password_hash(password)
check_password_hash(hash, password)
```

### 2. Sesiones
- Almacenamiento en filesystem (no recomendado para producción)
- En producción, usar Redis para sesiones

### 3. Clave de Emergencia 2FA
- Variable de entorno: `EMERGENCY_2FA_KEY`
- Cambiar en producción
- Mantener segura y fuera del código fuente

### 4. CORS
- Lista de orígenes permitidos configurable
- `supports_credentials=True` habilitado

---

## 🚀 Guía de Inicio Rápido

### 1. Requisitos Previos
```bash
Python 3.11+
MongoDB Atlas account
```

### 2. Instalación
```bash
# Clonar repositorio
git clone https://github.com/usuario/Restaurante-Callejon-9.git
cd Restaurante-Callejon-9

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configuración
```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar variables de entorno
# Importante: MONGO_URI y SECRET_KEY
```

### 4. Iniciar Servidor
```bash
python app.py
# Servidor en http://localhost:5000
```

### 5. Credenciales de Prueba
```
Email: admin@callejon9.com
Password: admin123
Rol: Administrador (1)
```

---

## 📝 Historial de Cambios

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0.0 | 2024 | Versión inicial con autenticación, 2FA, backup |
| 1.1.0 | 2024 | Agregado módulo de inventario |
| 1.2.0 | 2024 | Sistema de reportes con exportación |
| 2.0.0 | 2025 | Implementación CQRS, dashboard real |

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

---

**Documentación generada para el Sistema Restaurante Callejón 9**
**© 2026 - Todos los derechos reservados**
