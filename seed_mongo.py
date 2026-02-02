"""
Script para importar datos de ejemplo a MongoDB Atlas
Ejecutar: python import_seed_data.py
"""
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

if not MONGO_URI or not MONGO_DB_NAME:
    print("Error: Variables de entorno no configuradas")
    exit(1)

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

print("=" * 60)
print("IMPORTANDO DATOS DE EJEMPLO A MONGODB ATLAS")
print("=" * 60)

# Coleccion: mesas
print("\n[1/7] Importando mesas...")
mesas_data = [
    {
        "_id": ObjectId("697d82ff2a0a1055937a223d"),
        "numero": 1,
        "capacidad": 4,
        "estado": "disponible",
        "tipo": "interior",
        "seccion": "A",
        "activa": True,
        "created_at": datetime(2026, 1, 15, 10, 0, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a223e"),
        "numero": 2,
        "capacidad": 2,
        "estado": "ocupada",
        "tipo": "interior",
        "seccion": "A",
        "activa": True,
        "comensales_actuales": 2,
        "mesero_asignado": ObjectId("697d82ff2a0a1055937a2250"),
        "hora_inicio": datetime(2026, 1, 31, 14, 30, 0),
        "created_at": datetime(2026, 1, 15, 10, 0, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a223f"),
        "numero": 3,
        "capacidad": 6,
        "estado": "ocupada",
        "tipo": "interior",
        "seccion": "B",
        "activa": True,
        "comensales_actuales": 4,
        "mesero_asignado": ObjectId("697d82ff2a0a1055937a2251"),
        "hora_inicio": datetime(2026, 1, 31, 13, 45, 0),
        "created_at": datetime(2026, 1, 15, 10, 0, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2240"),
        "numero": 4,
        "capacidad": 4,
        "estado": "disponible",
        "tipo": "terraza",
        "seccion": "C",
        "activa": True,
        "created_at": datetime(2026, 1, 15, 10, 0, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2241"),
        "numero": 5,
        "capacidad": 8,
        "estado": "reservada",
        "tipo": "terraza",
        "seccion": "C",
        "activa": True,
        "reserva_hora": datetime(2026, 1, 31, 19, 0, 0),
        "reserva_nombre": "García Familia",
        "reserva_telefono": "5551234567",
        "created_at": datetime(2026, 1, 15, 10, 0, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2247"),
        "numero": 6,
        "capacidad": 4,
        "estado": "disponible",
        "tipo": "interior",
        "seccion": "A",
        "activa": True,
        "created_at": datetime(2026, 1, 15, 10, 0, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2248"),
        "numero": 7,
        "capacidad": 2,
        "estado": "disponible",
        "tipo": "interior",
        "seccion": "B",
        "activa": True,
        "created_at": datetime(2026, 1, 15, 10, 0, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2249"),
        "numero": 8,
        "capacidad": 6,
        "estado": "disponible",
        "tipo": "terraza",
        "seccion": "C",
        "activa": True,
        "created_at": datetime(2026, 1, 15, 10, 0, 0)
    }
]

try:
    db.mesas.drop()
    db.mesas.insert_many(mesas_data)
    print(f"   Insertadas {len(mesas_data)} mesas")
except Exception as e:
    print(f"   Error: {e}")

# Coleccion: comandas
print("\n[2/7] Importando comandas...")
comandas_data = [
    {
        "_id": ObjectId("697d82ff2a0a1055937a2242"),
        "numero_comanda": 1001,
        "mesa_id": ObjectId("697d82ff2a0a1055937a223e"),
        "mesa_numero": 2,
        "mesero_id": ObjectId("697d82ff2a0a1055937a2250"),
        "mesero_nombre": "Juan Pérez",
        "estado": "en_cocina",
        "comensales": 2,
        "platillos": [
            {
                "platillo_id": ObjectId("697d82ff2a0a1055937a2260"),
                "nombre": "Tacos al Pastor",
                "cantidad": 3,
                "precio_unitario": 45,
                "subtotal": 135,
                "notas": "Sin cebolla",
                "estado": "preparando"
            },
            {
                "platillo_id": ObjectId("697d82ff2a0a1055937a2261"),
                "nombre": "Quesadilla de Champiñones",
                "cantidad": 2,
                "precio_unitario": 35,
                "subtotal": 70,
                "notas": "",
                "estado": "preparando"
            }
        ],
        "subtotal": 205,
        "propina": 0,
        "total": 205,
        "created_at": datetime(2026, 1, 31, 14, 35, 0),
        "updated_at": datetime(2026, 1, 31, 14, 35, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2243"),
        "numero_comanda": 1002,
        "mesa_id": ObjectId("697d82ff2a0a1055937a223f"),
        "mesa_numero": 3,
        "mesero_id": ObjectId("697d82ff2a0a1055937a2251"),
        "mesero_nombre": "María López",
        "estado": "lista",
        "comensales": 4,
        "platillos": [
            {
                "platillo_id": ObjectId("697d82ff2a0a1055937a2262"),
                "nombre": "Enchiladas Suizas",
                "cantidad": 2,
                "precio_unitario": 55,
                "subtotal": 110,
                "notas": "",
                "estado": "listo"
            },
            {
                "platillo_id": ObjectId("697d82ff2a0a1055937a2263"),
                "nombre": "Sopes de Pollo",
                "cantidad": 2,
                "precio_unitario": 50,
                "subtotal": 100,
                "notas": "Extra salsa",
                "estado": "listo"
            }
        ],
        "subtotal": 210,
        "propina": 0,
        "total": 210,
        "created_at": datetime(2026, 1, 31, 13, 50, 0),
        "updated_at": datetime(2026, 1, 31, 14, 20, 0)
    }
]

try:
    db.comandas.drop()
    db.comandas.insert_many(comandas_data)
    print(f"   Insertadas {len(comandas_data)} comandas")
except Exception as e:
    print(f"   Error: {e}")

# Coleccion: ventas
print("\n[3/7] Importando ventas...")
ventas_data = [
    {
        "_id": ObjectId("697d82ff2a0a1055937a2244"),
        "numero_venta": 501,
        "mesa_numero": 1,
        "mesero_id": ObjectId("697d82ff2a0a1055937a2250"),
        "mesero_nombre": "Juan Pérez",
        "comensales": 2,
        "platillos": [
            {
                "nombre": "Guacamole",
                "cantidad": 1,
                "precio_unitario": 45,
                "subtotal": 45
            },
            {
                "nombre": "Tacos al Pastor",
                "cantidad": 4,
                "precio_unitario": 45,
                "subtotal": 180
            }
        ],
        "subtotal": 225,
        "propina": 22.50,
        "total": 247.50,
        "metodo_pago": "efectivo",
        "fecha": datetime(2026, 1, 31, 12, 30, 0),
        "created_at": datetime(2026, 1, 31, 12, 30, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2245"),
        "numero_venta": 502,
        "mesa_numero": 4,
        "mesero_id": ObjectId("697d82ff2a0a1055937a2251"),
        "mesero_nombre": "María López",
        "comensales": 3,
        "platillos": [
            {
                "nombre": "Quesadilla de Champiñones",
                "cantidad": 3,
                "precio_unitario": 35,
                "subtotal": 105
            },
            {
                "nombre": "Agua de Horchata",
                "cantidad": 3,
                "precio_unitario": 20,
                "subtotal": 60
            }
        ],
        "subtotal": 165,
        "propina": 16.50,
        "total": 181.50,
        "metodo_pago": "tarjeta",
        "fecha": datetime(2026, 1, 31, 11, 15, 0),
        "created_at": datetime(2026, 1, 31, 11, 15, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2246"),
        "numero_venta": 503,
        "mesa_numero": 2,
        "mesero_id": ObjectId("697d82ff2a0a1055937a2250"),
        "mesero_nombre": "Juan Pérez",
        "comensales": 4,
        "platillos": [
            {
                "nombre": "Enchiladas Suizas",
                "cantidad": 4,
                "precio_unitario": 55,
                "subtotal": 220
            },
            {
                "nombre": "Flan Napolitano",
                "cantidad": 2,
                "precio_unitario": 30,
                "subtotal": 60
            }
        ],
        "subtotal": 280,
        "propina": 28,
        "total": 308,
        "metodo_pago": "efectivo",
        "fecha": datetime(2026, 1, 31, 13, 0, 0),
        "created_at": datetime(2026, 1, 31, 13, 0, 0)
    }
]

try:
    db.ventas.drop()
    db.ventas.insert_many(ventas_data)
    print(f"   Insertadas {len(ventas_data)} ventas")
except Exception as e:
    print(f"   Error: {e}")

# Coleccion: platillos
print("\n[4/7] Importando platillos...")
platillos_data = [
    {
        "_id": ObjectId("697d82ff2a0a1055937a2260"),
        "nombre": "Tacos al Pastor",
        "descripcion": "3 tacos con piña y cilantro",
        "categoria": "tacos",
        "precio": 45,
        "disponible": True,
        "ingredientes": ["tortilla", "carne pastor", "piña", "cilantro", "cebolla"],
        "tiempo_preparacion": 10,
        "imagen": None,
        "created_at": datetime(2026, 1, 15, 10, 0, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2261"),
        "nombre": "Quesadilla de Champiñones",
        "descripcion": "Con queso Oaxaca",
        "categoria": "tacos",
        "precio": 35,
        "disponible": True,
        "ingredientes": ["tortilla", "queso oaxaca", "champiñones"],
        "tiempo_preparacion": 8,
        "imagen": None,
        "created_at": datetime(2026, 1, 15, 10, 0, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2262"),
        "nombre": "Enchiladas Suizas",
        "descripcion": "Bañadas en salsa verde con crema",
        "categoria": "principales",
        "precio": 55,
        "disponible": True,
        "ingredientes": ["tortilla", "pollo", "salsa verde", "queso", "crema"],
        "tiempo_preparacion": 15,
        "imagen": None,
        "created_at": datetime(2026, 1, 15, 10, 0, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2263"),
        "nombre": "Sopes de Pollo",
        "descripcion": "Con frijoles y lechuga",
        "categoria": "principales",
        "precio": 50,
        "disponible": True,
        "ingredientes": ["masa", "frijol", "pollo", "lechuga", "queso", "crema"],
        "tiempo_preparacion": 12,
        "imagen": None,
        "created_at": datetime(2026, 1, 15, 10, 0, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2264"),
        "nombre": "Guacamole",
        "descripcion": "Preparado al momento",
        "categoria": "entradas",
        "precio": 45,
        "disponible": True,
        "ingredientes": ["aguacate", "tomate", "cebolla", "cilantro", "limón"],
        "tiempo_preparacion": 5,
        "imagen": None,
        "created_at": datetime(2026, 1, 15, 10, 0, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2265"),
        "nombre": "Agua de Horchata",
        "descripcion": "Jarra 1L",
        "categoria": "bebidas",
        "precio": 20,
        "disponible": True,
        "ingredientes": ["arroz", "canela", "azúcar"],
        "tiempo_preparacion": 2,
        "imagen": None,
        "created_at": datetime(2026, 1, 15, 10, 0, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2266"),
        "nombre": "Flan Napolitano",
        "descripcion": "Casero",
        "categoria": "postres",
        "precio": 30,
        "disponible": True,
        "ingredientes": ["leche", "huevo", "azúcar", "vainilla"],
        "tiempo_preparacion": 3,
        "imagen": None,
        "created_at": datetime(2026, 1, 15, 10, 0, 0)
    }
]

try:
    db.platillos.drop()
    db.platillos.insert_many(platillos_data)
    print(f"   Insertadas {len(platillos_data)} platillos")
except Exception as e:
    print(f"   Error: {e}")

# Coleccion: actividad_reciente
print("\n[5/7] Importando actividad reciente...")
actividad_data = [
    {
        "_id": ObjectId("697d82ff2a0a1055937a2270"),
        "tipo": "venta_completada",
        "descripcion": "Mesa 5 cerrada por Juan Pérez",
        "usuario_id": ObjectId("697d82ff2a0a1055937a2250"),
        "usuario_nombre": "Juan Pérez",
        "mesa_numero": 5,
        "monto": 850,
        "timestamp": datetime(2026, 1, 31, 14, 28, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2271"),
        "tipo": "comanda_nueva",
        "descripcion": "Nueva comanda en Mesa 12",
        "usuario_id": ObjectId("697d82ff2a0a1055937a2251"),
        "usuario_nombre": "María López",
        "mesa_numero": 12,
        "timestamp": datetime(2026, 1, 31, 14, 25, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2272"),
        "tipo": "comanda_cocina",
        "descripcion": "Pedido enviado a cocina",
        "usuario_id": ObjectId("697d82ff2a0a1055937a2250"),
        "usuario_nombre": "Juan Pérez",
        "comanda_id": ObjectId("697d82ff2a0a1055937a2242"),
        "timestamp": datetime(2026, 1, 31, 14, 22, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2273"),
        "tipo": "pago_recibido",
        "descripcion": "Pago recibido: $850 (Tarjeta)",
        "usuario_id": ObjectId("697d82ff2a0a1055937a2250"),
        "usuario_nombre": "Juan Pérez",
        "monto": 850,
        "metodo_pago": "tarjeta",
        "timestamp": datetime(2026, 1, 31, 14, 20, 0)
    }
]

try:
    db.actividad_reciente.drop()
    db.actividad_reciente.insert_many(actividad_data)
    print(f"   Insertadas {len(actividad_data)} actividades")
except Exception as e:
    print(f"   Error: {e}")

# Coleccion: estadisticas_diarias
print("\n[6/7] Importando estadísticas diarias...")
estadisticas_data = [
    {
        "_id": ObjectId("697d82ff2a0a1055937a2280"),
        "fecha": datetime(2026, 1, 31, 0, 0, 0),
        "ventas_totales": 12450,
        "numero_ventas": 45,
        "ticket_promedio": 276.67,
        "propinas_totales": 1245,
        "mesas_atendidas": 38,
        "platillos_vendidos": {
            "Tacos al Pastor": 32,
            "Quesadilla de Champiñones": 25,
            "Enchiladas Suizas": 18,
            "Guacamole": 15
        },
        "metodos_pago": {
            "efectivo": 7200,
            "tarjeta": 4500,
            "transferencia": 750
        },
        "ventas_por_hora": [
            {"hora": 11, "ventas": 850},
            {"hora": 12, "ventas": 1200},
            {"hora": 13, "ventas": 2100},
            {"hora": 14, "ventas": 3200},
            {"hora": 15, "ventas": 2500},
            {"hora": 16, "ventas": 1800},
            {"hora": 17, "ventas": 800}
        ],
        "updated_at": datetime(2026, 1, 31, 14, 30, 0)
    }
]

try:
    db.estadisticas_diarias.drop()
    db.estadisticas_diarias.insert_many(estadisticas_data)
    print(f"   Insertadas {len(estadisticas_data)} estadísticas")
except Exception as e:
    print(f"   Error: {e}")

# Coleccion: configuracion_sistema
print("\n[7/7] Importando configuración del sistema...")
config_data = [
    {
        "_id": ObjectId("697d82ff2a0a1055937a2290"),
        "clave": "backup_automatico",
        "valor": {
            "enabled": False,
            "frequency": "diaria",
            "hora": "02:00",
            "retener_dias": 30
        },
        "updated_at": datetime(2026, 1, 31, 14, 30, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2291"),
        "clave": "modo_mantenimiento",
        "valor": False,
        "updated_at": datetime(2026, 1, 31, 14, 30, 0)
    },
    {
        "_id": ObjectId("697d82ff2a0a1055937a2292"),
        "clave": "aceptar_reservas",
        "valor": True,
        "updated_at": datetime(2026, 1, 31, 14, 30, 0)
    }
]

try:
    db.configuracion_sistema.drop()
    db.configuracion_sistema.insert_many(config_data)
    print(f"   Insertadas {len(config_data)} configuraciones")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 60)
print("IMPORTACION COMPLETADA CON EXITO")
print("=" * 60)
print(f"\nBase de datos: {MONGO_DB_NAME}")
print(f"Colecciones creadas: 7")
print("\nPuedes verificar los datos en MongoDB Atlas")
print("=" * 60)

client.close()