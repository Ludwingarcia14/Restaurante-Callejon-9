#!/usr/bin/env python3
"""
Script de Limpieza de Proyecto PyME → Restaurante
Ejecutar desde la raíz del proyecto: python cleanup_pyme_project.py
"""

import os
import shutil
from pathlib import Path

# ============================================
# CONFIGURACIÓN DE RUTAS A ELIMINAR
# ============================================

DIRS_TO_DELETE = [
    # Modelos PyME
    "models/clienteModel.py",
    "models/financiera.py",
    "models/credito.py",
    "models/asesor_asignado.py",
    "models/documentofisica_model.py",
    "models/documentomoral_model.py",
    "models/landing_model.py",
    "models/estados_model.py",
    
    # Controladores PyME
    "controllers/financiera",
    "controllers/asesor",
    "controllers/client",
    "controllers/ia",
    "controllers/admin",
    
    # Servicios IA PyME
    "services/ai_engine",
    "services/scoring",
    "services/proyecciones",
    "services/setup",
    "services/trained_model",
    
    # CQRS PyME
    "cqrs/commands/financiera",
    "cqrs/commands/asesor",
    "cqrs/commands/client",
    "cqrs/commands/prestamos",
    "cqrs/queryes/financiera",
    "cqrs/queryes/asesor",
    "cqrs/queryes/client",
    "cqrs/queryes/prestamos",
    "cqrs/queryes/ia",
    
    # Vistas PyME
    "resources/views/admin",
    "resources/views/asesor",
    "resources/views/client",
    "resources/views/financieras",
    "resources/views/auth/register_client.html",
    "resources/views/auth/retrievepassword.html",
    "resources/views/layout/layout_financieras.html",
    "resources/views/layout/layout_asesor.html",
    "resources/views/layout/layout_cliente.html",
    "resources/views/aviso_privacidad.html",
    "resources/views/ciec.html",
    "resources/views/login_client.html",
    
    # Utilidades PyME
    "utils/background_tasks_buro.py",
    "utils/background_tasks_domicilio.py",
    "utils/parsers.py",
    
    # Assets PyME
    "static/uploads/fisica",
    "static/temp_uploads/txt_analysis",
    "static/img/carousel",
]

FILES_TO_CLEAN = [
    "routes.py",
    "app.py",
    "README.md",
    ".env.example",
]

# ============================================
# FUNCIONES DE LIMPIEZA
# ============================================

def delete_path(path_str):
    """Elimina archivo o directorio de forma segura"""
    path = Path(path_str)
    
    if not path.exists():
        print(f"⚠️  No existe: {path}")
        return
    
    try:
        if path.is_file():
            path.unlink()
            print(f"✅ Eliminado archivo: {path}")
        elif path.is_dir():
            shutil.rmtree(path)
            print(f"✅ Eliminado directorio: {path}")
    except Exception as e:
        print(f"❌ Error eliminando {path}: {e}")


def clean_pycache():
    """Elimina todos los __pycache__ del proyecto"""
    print("\n🧹 Limpiando archivos __pycache__...")
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            pycache_path = Path(root) / "__pycache__"
            try:
                shutil.rmtree(pycache_path)
                print(f"✅ Eliminado: {pycache_path}")
            except Exception as e:
                print(f"❌ Error: {e}")


def create_new_structure():
    """Crea la estructura base para el sistema de restaurante"""
    print("\n📁 Creando estructura para Restaurante...")
    
    dirs_to_create = [
        # Modelos
        "models",
        
        # Controladores
        "controllers/menu",
        "controllers/inventario",
        "controllers/venta",
        "controllers/mesa",
        
        # CQRS
        "cqrs/commands/menu",
        "cqrs/commands/inventario",
        "cqrs/commands/venta",
        "cqrs/queryes/menu",
        "cqrs/queryes/inventario",
        "cqrs/queryes/venta",
        
        # Servicios Analytics
        "services/analytics",
        
        # Vistas
        "resources/views/admin/menu",
        "resources/views/admin/inventario",
        "resources/views/admin/ventas",
        "resources/views/mesero",
        "resources/views/cocina",
        "resources/views/layout",
        "resources/views/auth",
    ]
    
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Crear __init__.py en carpetas Python
        if not dir_path.startswith("resources"):
            init_file = Path(dir_path) / "__init__.py"
            init_file.touch(exist_ok=True)
    
    print("✅ Estructura base creada")


def create_placeholder_files():
    """Crea archivos placeholder para la nueva estructura"""
    print("\n📝 Creando archivos base...")
    
    placeholders = {
        # Modelos
        "models/menu_model.py": '''"""
Modelo de Menú - Platillos, Categorías, Recetas
"""
from config.db import db
from datetime import datetime
from bson.objectid import ObjectId

class Platillo:
    collection = db["platillos"]
    
    @classmethod
    def find_all(cls):
        return list(cls.collection.find())
    
    @classmethod
    def find_by_id(cls, id):
        return cls.collection.find_one({"_id": ObjectId(id)})
''',
        
        "models/inventario_model.py": '''"""
Modelo de Inventario - Insumos, Stock, Movimientos
"""
from config.db import db
from datetime import datetime

class Insumo:
    collection = db["insumos"]
    
    @classmethod
    def find_all(cls):
        return list(cls.collection.find())
''',
        
        "models/venta_model.py": '''"""
Modelo de Ventas - Comandas, Ventas, Pagos
"""
from config.db import db
from datetime import datetime

class Venta:
    collection = db["ventas"]
    
    @classmethod
    def find_all(cls):
        return list(cls.collection.find())
''',
        
        "models/mesa_model.py": '''"""
Modelo de Mesas - Estado y Asignación
"""
from config.db import db

class Mesa:
    collection = db["mesas"]
    
    @classmethod
    def find_all(cls):
        return list(cls.collection.find())
''',
        
        # Controladores
        "controllers/menu/menuController.py": '''"""
Controlador de Menú
"""
from flask import render_template, session, redirect, url_for

class MenuController:
    @staticmethod
    def index():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))
        return render_template("admin/menu/lista.html")
''',
        
        # README actualizado
        "README.md": '''# 🍽️ Callejón 9 – Sistema Integral de Gestión para Restaurantes

Sistema modular de gestión gastronómica con analítica avanzada mediante Apache Spark.

## 🏗️ Arquitectura

```
Datos MongoDB → Extracción → Spark DF → Limpieza → Métricas → JSON
```

## 🌟 Características

### 📋 Gestión de Menú
- Control de platillos y recetas
- Categorías y subcategorías
- Vinculación con inventarios

### 📦 Inventarios
- Control de insumos (kg, lts, piezas)
- Trazabilidad automática
- Alertas de stock crítico

### 💳 Ventas y Comandas
- Sistema de comandas optimizado
- Múltiples métodos de pago
- Integración con cocina

### 🔐 Seguridad RBAC
- Roles: Administrador, Mesero, Cocina
- Autenticación JWT

## 📈 Módulo de Analítica (Spark)

Transformación de datos en inteligencia de negocios:

- 💰 Volumen de ventas (diario, semanal, mensual)
- 🎫 Promedio de ticket
- 🔥 Platillos más vendidos
- 📉 Análisis de picos operativos

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| Backend | Python 3.11 + Flask |
| Base de Datos | MongoDB |
| Analítica | Apache Spark |
| Frontend | React/Next.js |

## 🚀 Instalación

```bash
# Clonar repositorio
git clone [URL]
cd Restaurante-Callejon-9

# Crear entorno
conda create -n Callejon9 python=3.11 -y
conda activate Callejon9

# Instalar dependencias
pip install -r requirements.txt

# Configurar .env
cp .env.example .env

# Ejecutar
python app.py
```

## 👥 Equipo

- **Ludwin Garcia Gaytan** - Arquitectura y Liderazgo Técnico

## 📄 Licencia

MIT License
''',
    }
    
    for file_path, content in placeholders.items():
        path = Path(file_path)
        if not path.exists():
            path.write_text(content)
            print(f"✅ Creado: {file_path}")


def main():
    """Función principal de limpieza"""
    print("=" * 60)
    print("🧹 INICIANDO LIMPIEZA DE PROYECTO PyME → RESTAURANTE")
    print("=" * 60)
    
    # Confirmación de seguridad
    print("\n⚠️  ADVERTENCIA: Este script eliminará archivos permanentemente")
    respuesta = input("¿Deseas continuar? (escribe 'SI' para confirmar): ")
    
    if respuesta != "SI":
        print("❌ Operación cancelada")
        return
    
    # Fase 1: Eliminar archivos y carpetas PyME
    print("\n📦 FASE 1: Eliminando archivos PyME...")
    for path_str in DIRS_TO_DELETE:
        delete_path(path_str)
    
    # Fase 2: Limpiar __pycache__
    clean_pycache()
    
    # Fase 3: Crear nueva estructura
    create_new_structure()
    
    # Fase 4: Crear archivos placeholder
    create_placeholder_files()
    
    print("\n" + "=" * 60)
    print("✅ LIMPIEZA COMPLETADA")
    print("=" * 60)
    print("\n📋 PASOS SIGUIENTES:")
    print("1. Revisar y actualizar routes.py")
    print("2. Revisar y actualizar app.py")
    print("3. Actualizar .env con configuración del restaurante")
    print("4. Implementar lógica de negocio en los nuevos controladores")
    print("5. Crear vistas HTML para el sistema de restaurante")
    print("\n🎉 El proyecto está listo para comenzar el desarrollo del restaurante")


if __name__ == "__main__":
    main()