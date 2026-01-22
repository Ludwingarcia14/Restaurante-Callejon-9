# 🍽️ Callejón 9 – Sistema Integral de Gestión para Restaurantes

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-green.svg)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)
![MongoDB](https://img.shields.io/badge/database-MongoDB-47A248.svg)
![Apache Spark](https://img.shields.io/badge/analytics-Apache%20Spark-E25A1C.svg)

**Callejón 9** es una plataforma modular de alto rendimiento diseñada para centralizar la operación gastronómica. Su arquitectura orientada a servicios permite una gestión eficiente desde la toma de pedidos hasta el análisis de datos masivos mediante Spark.

---

## 🏗️ Arquitectura del Sistema

El proyecto sigue un flujo de datos estructurado para garantizar que la lógica de negocio esté separada de la analítica pesada.

Datos en MongoDB
        │
        ▼
Extracción y Conversión
        │
        ▼
Cargas a Spark DF
        │
        ▼
Limpieza y Formateo de Campos
        │
        ▼
Cálculos y Métricas
        │
        ▼
Reporte final en JSON

## 🌟 Características Principales

### 📋 Gestión de Menú
* **Control Total:** Registro y edición de platillos con gestión de recetas.
* **Organización:** Administración por categorías y subcategorías.
* **Ingredientes:** Vinculación directa con el módulo de inventarios.

### 📦 Inventarios
* **Unidades de Medida:** Control preciso de insumos (kg, lts, piezas).
* **Trazabilidad:** Registro automático de entradas y salidas.
* **Stock Crítico:** Alertas automáticas cuando los insumos bajan de los mínimos establecidos.

### 💳 Ventas y Comandas
* **Agilidad:** Captura de pedidos optimizada para dispositivos táctiles.
* **Integración:** Comunicación inmediata con el área de cocina.
* **Finanzas:** Cálculo automático de totales y gestión de múltiples métodos de pago.

### 🔐 Seguridad y Roles
* **RBAC (Role-Based Access Control):** Permisos específicos para Administrador, Mesero y Cocina.
* **Autenticación:** Sistema basado en tokens JWT (JSON Web Tokens).

---

## 📈 Módulo de Analítica (Spark)
> **Ubicación:** `app/services/analytics/`

Este módulo transforma los datos crudos de MongoDB en **inteligencia de negocios** mediante el motor de procesamiento distribuido Apache Spark.



**Métricas Clave Generadas:**
* 💰 **Volumen de Ventas:** Análisis diario, semanal y mensual.
* 🎫 **Promedio de Ticket:** Valor promedio de consumo por mesa.
* 🔥 **Platillos Estrella:** Identificación de los productos más vendidos.
* 📉 **Picos Operativos:** Detección de horas de mayor carga de trabajo.

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
| :--- | :--- |
| **Lenguaje** | `Python 3.11` |
| **Backend Framework** | `FastAPI` |
| **Base de Datos** | `MongoDB` |
| **Motor de Analítica** | `Apache Spark` |
| **Frontend** | `React / Next.js` |
| **Entorno** | `Conda / Docker` |

---

## 📁 Estructura del Proyecto

```text
├── app/
│   ├── api/           # Rutas y Controladores de FastAPI
│   ├── services/      # Lógica de Negocio (Menú, Ventas, Inventarios)
│   ├── analytics/     # Motor Spark y Procesamiento de Datos
│   ├── models/        # Esquemas de Datos
│   └── database/      # Configuración de MongoDB
├── config/            # Variables de entorno y ajustes
├── docs/              # Documentación técnica adicional
├── frontend/          # Interfaz de usuario (React/Next.js)
├── app.py             # Punto de entrada de la aplicación
└── requirements.txt   # Dependencias del sistema

🚀 Instalación y Despliegue
Sigue estos pasos para configurar tu entorno local con Conda:

Clonar el repositorio:

git clone [https://github.com/Ludwingarcia14/Restaurante-Callejon-9.git]
cd Restaurante-Callejon-9

Configurar el entorno virtual:
conda create -n Callejon9 python=3.11 -y
conda activate Callejon9

Instalar dependencias:
pip install -r requirements.txt

Configurar variables de entorno:
cp .env.example .env
# Edita el archivo .env con tus credenciales de MongoDB

Ejecutar la aplicación:
python app.py

👥 Equipo de Desarrollo

🏛️ Dirección y Liderazgo Técnico
Ludwin Garcia Gaytan

Rol: Arquitectura, Coordinación y Supervisión General.

👨‍💻 Contributors
Duarte Villavicencio Octavio - Developer

Mercado Cerrano Valeria - Developer

Ibarra Alba Regina - Developer

📄 Licencia
Este proyecto está bajo la licencia MIT. Para más detalles, consulta el archivo LICENSE.

Callejón 9 – Optimizando el sabor a través de los datos.