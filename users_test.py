#!/usr/bin/env python3
"""
Script para insertar usuarios de prueba en MongoDB
Ejecutar: python insert_test_users.py
"""
from dotenv import load_dotenv
load_dotenv()

from config.db import db
from datetime import datetime
from bson.objectid import ObjectId

def insert_test_users():
    """Inserta usuarios de prueba con contraseñas en texto plano"""
    
    usuarios_prueba = [
        {
            # ADMINISTRADOR
            "usuario_nombre": "Ludwin",
            "usuario_apellidos": "Garcia Gaytan",
            "usuario_email": "lud.dev@gmail.com",
            "usuario_clave": "admin123",  # Contraseña en texto plano
            "usuario_rol": "1",  # Admin
            "usuario_telefono": "7221234567",
            "usuario_foto": None,
            "usuario_status": 1,  # Activo
            "usuario_tokensession": None,
            "2fa_enabled": False,
            "2fa_tipo": None,
            "2fa_secret": None,
            "2fa_telefono": None,
            "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.utcnow()
        },
        {
            # MESERO
            "usuario_nombre": "Octavio",
            "usuario_apellidos": "Duarte Villavicencio",
            "usuario_email": "octavio@admin.com",
            "usuario_clave": "mesero123",  # Contraseña en texto plano
            "usuario_rol": "2",  # Mesero
            "usuario_telefono": "7229876543",
            "usuario_foto": None,
            "usuario_status": 1,  # Activo
            "usuario_tokensession": None,
            "2fa_enabled": False,
            "2fa_tipo": None,
            "2fa_secret": None,
            "2fa_telefono": None,
            # Datos específicos de mesero
            "mesero_numero": "M001",
            "mesero_turno": "matutino",
            "mesero_mesas": ["1", "2", "3", "4"],
            "mesero_puede_cerrar_cuenta": True,
            "mesero_puede_aplicar_descuento": False,
            "mesero_propina_sugerida": 10,
            "mesero_propina_acumulada_dia": 0,
            "mesero_ventas_promedio_dia": 0,
            "mesero_calificacion_cliente": 0,
            "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.utcnow()
        },
        {
            # COCINA
            "usuario_nombre": "Regina",
            "usuario_apellidos": "Ibarra Alba",
            "usuario_email": "regi@admin.com",
            "usuario_clave": "cocina123",  # Contraseña en texto plano
            "usuario_rol": "3",  # Cocina
            "usuario_telefono": "7225551234",
            "usuario_foto": None,
            "usuario_status": 1,  # Activo
            "usuario_tokensession": None,
            "2fa_enabled": False,
            "2fa_tipo": None,
            "2fa_secret": None,
            "2fa_telefono": None,
            # Datos específicos de cocina
            "cocina_numero": "C001",
            "cocina_puesto": "cocinero",
            "cocina_area": "parrilla",
            "cocina_turno": "matutino",
            "cocina_especialidad": ["carnes", "asados"],
            "cocina_puede_modificar_menu": False,
            "cocina_puede_ver_recetas_completas": True,
            "cocina_certificaciones": ["manejo_higiénico", "cortes_carne"],
            "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.utcnow()
        }
    ]
    
    print("=" * 60)
    print("👥 INSERTANDO USUARIOS DE PRUEBA")
    print("=" * 60)
    
    # Verificar BD existente
    try:
        from pymongo import MongoClient
        import os
        client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
        databases = client.list_database_names()
        print(f"\n📊 Bases de datos disponibles: {databases}")
        
        if "Callejon9" in databases:
            print("\n⚠️  ADVERTENCIA: Existe una BD 'Callejon9' (mayúscula)")
            print("   Ejecuta primero: python fix_mongodb.py")
            return
        
        client.close()
    except Exception as e:
        print(f"⚠️  Advertencia al verificar BD: {e}")
    
    # Limpiar usuarios existentes (opcional)
    respuesta = input("\n⚠️  ¿Deseas eliminar usuarios existentes antes de insertar? (SI/NO): ")
    if respuesta.upper() == "SI":
        try:
            result = db.usuarios.delete_many({})
            print(f"   ✅ {result.deleted_count} usuarios eliminados")
        except Exception as e:
            print(f"   ⚠️  Error al eliminar: {e}")
    
    # Insertar usuarios
    for usuario in usuarios_prueba:
        try:
            # Verificar si el usuario ya existe
            existe = db.usuarios.find_one({"usuario_email": usuario["usuario_email"]})
            
            if existe:
                print(f"\n⚠️  Usuario {usuario['usuario_email']} ya existe")
                actualizar = input("   ¿Deseas actualizarlo? (SI/NO): ")
                if actualizar.upper() == "SI":
                    db.usuarios.update_one(
                        {"usuario_email": usuario["usuario_email"]},
                        {"$set": usuario}
                    )
                    print(f"   ✅ Usuario actualizado: {usuario['usuario_nombre']}")
            else:
                result = db.usuarios.insert_one(usuario)
                print(f"   ✅ Usuario creado: {usuario['usuario_nombre']} ({usuario['usuario_email']})")
        except Exception as e:
            print(f"   ❌ Error al insertar {usuario['usuario_email']}: {e}")
            continue
    
    print("\n" + "=" * 60)
    print("✅ PROCESO COMPLETADO")
    print("=" * 60)
    print("\n📋 CREDENCIALES DE ACCESO:\n")
    print("👔 ADMINISTRADOR:")
    print("   Email: lud.dev@gmail.com")
    print("   Password: admin123")
    print("\n🍽️  MESERO:")
    print("   Email: octavio@admin.com")
    print("   Password: mesero123")
    print("\n👨‍🍳 COCINA:")
    print("   Email: regi@admin.com")
    print("   Password: cocina123")
    print("\n" + "=" * 60)
    print("🚀 Ahora puedes ejecutar: python app.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        insert_test_users()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()