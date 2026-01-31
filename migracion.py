#!/usr/bin/env python3
"""
Script de Migración - Rol de Inventario
Crea usuario de prueba y datos iniciales
"""
import bcrypt
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Conectar a MongoDB
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

if not MONGO_URI or not MONGO_DB_NAME:
    raise ValueError("MONGO_URI and MONGO_DB_NAME environment variables must be set")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

print("=" * 60)
print("🔧 MIGRACIÓN: ROL DE INVENTARIO")
print("=" * 60)

# ==========================================
# 1. CREAR USUARIO DE INVENTARIO
# ==========================================

print("\n1️⃣ Creando usuario de prueba para inventario...")

# Verificar si ya existe
usuario_existente = db.usuarios.find_one({"usuario_email": "inventario@callejon9.com"})

if usuario_existente:
    print("⚠️  Usuario ya existe, actualizando...")
    usuario_id = usuario_existente["_id"]
else:
    # Hashear contraseña
    password = "inventario123"
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    # Crear usuario
    usuario = {
        "usuario_nombre": "Valeria",
        "usuario_apellidos": "Mercado Cerrano",
        "usuario_email": "inventario@callejon9.com",
        "usuario_clave": hashed,
        "usuario_rol": "4",  # Inventario
        "usuario_telefono": "7221234567",
        "usuario_foto": None,
        "usuario_status": 1,  # Activo
        "usuario_tokensession": None,
        "2fa_enabled": False,
        "2fa_tipo": None,
        "2fa_secret": None,
        "2fa_telefono": None,
        
        # Campos específicos de inventario
        "inventario_numero": "INV-001",
        "inventario_turno": "matutino",
        "inventario_area_responsabilidad": "almacen_general",
        "inventario_puede_autorizar_mermas": True,
        "inventario_limite_ajustes": 1000,  # Límite en pesos para ajustes sin autorización
        
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.utcnow()
    }
    
    result = db.usuarios.insert_one(usuario)
    usuario_id = result.inserted_id
    print(f"✅ Usuario creado: inventario@callejon9.com")
    print(f"   Contraseña: {password}")
    print(f"   ID: {usuario_id}")

# ==========================================
# 2. CREAR PROVEEDORES DE PRUEBA
# ==========================================

print("\n2️⃣ Creando proveedores de prueba...")

proveedores_data = [
    {
        "nombre": "Comercializadora de Carnes del Valle",
        "razon_social": "Comercializadora de Carnes del Valle S.A. de C.V.",
        "rfc": "CCV123456789",
        "telefono": "7221111111",
        "email": "ventas@carnesvalle.com",
        "direccion": "Av. Principal 123, Valle de Bravo",
        "contacto_nombre": "Juan Pérez",
        "contacto_telefono": "7221111112",
        "activo": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Verduras Frescas del Sur",
        "razon_social": "Verduras Frescas del Sur S.A.",
        "rfc": "VFS987654321",
        "telefono": "7222222222",
        "email": "pedidos@verdurasfrescas.com",
        "direccion": "Carretera Sur Km 5, Valle de Bravo",
        "contacto_nombre": "María González",
        "contacto_telefono": "7222222223",
        "activo": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Lácteos y Derivados La Granja",
        "razon_social": "Lácteos La Granja S.C.",
        "rfc": "LGR456789123",
        "telefono": "7223333333",
        "email": "contacto@lacteoslagranja.com",
        "direccion": "Camino Real 45, Valle de Bravo",
        "contacto_nombre": "Carlos Ramírez",
        "contacto_telefono": "7223333334",
        "activo": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

proveedores_ids = []
for prov in proveedores_data:
    # Verificar si ya existe
    existente = db.proveedores.find_one({"rfc": prov["rfc"]})
    if existente:
        print(f"⚠️  Proveedor ya existe: {prov['nombre']}")
        proveedores_ids.append(existente["_id"])
    else:
        result = db.proveedores.insert_one(prov)
        proveedores_ids.append(result.inserted_id)
        print(f"✅ Proveedor creado: {prov['nombre']}")

# ==========================================
# 3. CREAR INSUMOS DE PRUEBA
# ==========================================

print("\n3️⃣ Creando insumos de prueba...")

insumos_data = [
    # Carnes
    {
        "nombre": "Carne de Res (Bistec)",
        "categoria": "carnes",
        "unidad_medida": "kg",
        "stock_actual": 15.5,
        "stock_minimo": 10.0,
        "costo_unitario": 180.00,
        "proveedor_id": proveedores_ids[0],
        "activo": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Pechuga de Pollo",
        "categoria": "carnes",
        "unidad_medida": "kg",
        "stock_actual": 8.0,
        "stock_minimo": 12.0,  # Stock crítico
        "costo_unitario": 95.00,
        "proveedor_id": proveedores_ids[0],
        "activo": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    # Verduras
    {
        "nombre": "Lechuga Romana",
        "categoria": "verduras",
        "unidad_medida": "pza",
        "stock_actual": 25,
        "stock_minimo": 20,
        "costo_unitario": 15.00,
        "proveedor_id": proveedores_ids[1],
        "activo": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Tomate Bola",
        "categoria": "verduras",
        "unidad_medida": "kg",
        "stock_actual": 5.0,
        "stock_minimo": 8.0,  # Stock crítico
        "costo_unitario": 22.00,
        "proveedor_id": proveedores_ids[1],
        "activo": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    # Lácteos
    {
        "nombre": "Queso Manchego",
        "categoria": "lacteos",
        "unidad_medida": "kg",
        "stock_actual": 3.5,
        "stock_minimo": 5.0,  # Stock crítico
        "costo_unitario": 180.00,
        "proveedor_id": proveedores_ids[2],
        "activo": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Leche Entera",
        "categoria": "lacteos",
        "unidad_medida": "lt",
        "stock_actual": 20.0,
        "stock_minimo": 15.0,
        "costo_unitario": 18.50,
        "proveedor_id": proveedores_ids[2],
        "activo": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    # Condimentos
    {
        "nombre": "Sal de Grano",
        "categoria": "condimentos",
        "unidad_medida": "kg",
        "stock_actual": 8.0,
        "stock_minimo": 5.0,
        "costo_unitario": 12.00,
        "proveedor_id": proveedores_ids[0],
        "activo": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "nombre": "Aceite Vegetal",
        "categoria": "condimentos",
        "unidad_medida": "lt",
        "stock_actual": 2.0,
        "stock_minimo": 5.0,  # Stock crítico
        "costo_unitario": 45.00,
        "proveedor_id": proveedores_ids[0],
        "activo": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

insumos_ids = []
for insumo in insumos_data:
    # Verificar si ya existe
    existente = db.insumos.find_one({"nombre": insumo["nombre"]})
    if existente:
        print(f"⚠️  Insumo ya existe: {insumo['nombre']}")
        insumos_ids.append(existente["_id"])
    else:
        result = db.insumos.insert_one(insumo)
        insumos_ids.append(result.inserted_id)
        print(f"✅ Insumo creado: {insumo['nombre']} - Stock: {insumo['stock_actual']} {insumo['unidad_medida']}")

# ==========================================
# 4. GENERAR ALERTAS DE STOCK CRÍTICO
# ==========================================

print("\n4️⃣ Generando alertas de stock crítico...")

# Buscar insumos con stock por debajo del mínimo
insumos_criticos = db.insumos.find({
    "activo": True,
    "$expr": {"$lte": ["$stock_actual", "$stock_minimo"]}
})

alertas_creadas = 0
for insumo in insumos_criticos:
    # Verificar si ya existe alerta
    alerta_existente = db.alertas_stock.find_one({
        "insumo_id": insumo["_id"],
        "resuelta": False
    })
    
    if not alerta_existente:
        diferencia = insumo["stock_minimo"] - insumo["stock_actual"]
        
        # Calcular criticidad
        if insumo["stock_actual"] == 0:
            nivel = "alta"
        elif insumo["stock_actual"] <= insumo["stock_minimo"] * 0.5:
            nivel = "alta"
        elif insumo["stock_actual"] <= insumo["stock_minimo"] * 0.8:
            nivel = "media"
        else:
            nivel = "baja"
        
        alerta = {
            "insumo_id": insumo["_id"],
            "insumo_nombre": insumo["nombre"],
            "stock_actual": insumo["stock_actual"],
            "stock_minimo": insumo["stock_minimo"],
            "diferencia": diferencia,
            "nivel_criticidad": nivel,
            "resuelta": False,
            "fecha_generacion": datetime.utcnow(),
            "fecha_resolucion": None
        }
        
        db.alertas_stock.insert_one(alerta)
        alertas_creadas += 1
        print(f"🚨 Alerta creada: {insumo['nombre']} - Nivel: {nivel}")

print(f"✅ Total de alertas creadas: {alertas_creadas}")

# ==========================================
# 5. CREAR MOVIMIENTOS DE EJEMPLO
# ==========================================

print("\n5️⃣ Creando movimientos de ejemplo...")

# Solo crear si no existen movimientos
movimientos_existentes = db.movimientos_inventario.count_documents({})

if movimientos_existentes == 0:
    movimientos_ejemplo = [
        {
            "tipo": "entrada",
            "insumo_id": insumos_ids[0],
            "insumo_nombre": "Carne de Res (Bistec)",
            "cantidad": 10.0,
            "unidad_medida": "kg",
            "stock_anterior": 5.5,
            "stock_nuevo": 15.5,
            "costo_unitario": 180.00,
            "costo_total": 1800.00,
            "usuario_id": usuario_id,
            "proveedor_id": proveedores_ids[0],
            "motivo": "Compra semanal",
            "referencia": "FAC-2025-001",
            "fecha": datetime.utcnow()
        },
        {
            "tipo": "salida",
            "insumo_id": insumos_ids[2],
            "insumo_nombre": "Lechuga Romana",
            "cantidad": 5.0,
            "unidad_medida": "pza",
            "stock_anterior": 30,
            "stock_nuevo": 25,
            "costo_unitario": 15.00,
            "costo_total": 75.00,
            "usuario_id": usuario_id,
            "proveedor_id": None,
            "motivo": "Consumo cocina",
            "referencia": "",
            "fecha": datetime.utcnow()
        }
    ]
    
    for mov in movimientos_ejemplo:
        db.movimientos_inventario.insert_one(mov)
        print(f"✅ Movimiento creado: {mov['tipo']} - {mov['insumo_nombre']}")
else:
    print("⚠️  Ya existen movimientos, omitiendo...")

# ==========================================
# RESUMEN FINAL
# ==========================================

print("\n" + "=" * 60)
print("✅ MIGRACIÓN COMPLETADA")
print("=" * 60)
print("\n📋 RESUMEN:")
print(f"   👤 Usuario: inventario@callejon9.com")
print(f"   🔑 Contraseña: inventario123")
print(f"   🏷️  Rol: Encargado de Inventario (4)")
print(f"\n   📦 Insumos creados: {len(insumos_ids)}")
print(f"   🚚 Proveedores creados: {len(proveedores_ids)}")
print(f"   🚨 Alertas activas: {alertas_creadas}")
print("\n" + "=" * 60)
print("🚀 Puedes iniciar sesión con las credenciales arriba")
print("=" * 60 + "\n")