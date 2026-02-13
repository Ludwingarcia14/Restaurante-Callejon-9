"""
Verificar mesas asignadas al mesero
"""

from config.db import db

print("=" * 60)
print("🔍 VERIFICACIÓN DE MESAS ASIGNADAS")
print("=" * 60)

# Buscar el usuario mesero actual (Octavio según los logs)
usuario = db.usuarios.find_one({"usuario_nombre": "Octavio", "usuario_rol": "2"})

if usuario:
    print(f"\n✅ Usuario encontrado: {usuario.get('usuario_nombre')}")
    print(f"   Email: {usuario.get('usuario_email')}")
    print(f"   Rol: {usuario.get('usuario_rol')}")
    
    # Verificar si tiene mesas asignadas
    if "mesero_mesas" in usuario:
        mesas = usuario.get("mesero_mesas", [])
        print(f"\n📋 Mesas asignadas: {mesas}")
        print(f"   Total: {len(mesas)} mesas")
        
        # Verificar que esas mesas existan en la colección
        print(f"\n🔍 Verificando que las mesas existan en la BD:")
        for num_mesa in mesas:
            mesa = db.mesas.find_one({"numero": str(num_mesa)})
            if mesa:
                print(f"   ✅ Mesa {num_mesa}: {mesa.get('estado')} - {mesa.get('tipo')}")
            else:
                print(f"   ❌ Mesa {num_mesa}: NO EXISTE EN LA BD")
    else:
        print(f"\n❌ El usuario NO tiene el campo 'mesero_mesas'")
        print(f"\n📝 Campos del usuario:")
        for key in usuario.keys():
            if key.startswith('mesero'):
                print(f"   - {key}: {usuario.get(key)}")
else:
    print("\n❌ No se encontró el usuario 'Octavio' con rol mesero")

# Ver todas las mesas disponibles
print(f"\n" + "=" * 60)
print("📊 TODAS LAS MESAS EN LA BASE DE DATOS")
print("=" * 60)

mesas_bd = list(db.mesas.find({"activa": True}))
print(f"\nTotal de mesas: {len(mesas_bd)}")

for mesa in mesas_bd:
    print(f"   Mesa {mesa.get('numero')}: {mesa.get('estado')} - {mesa.get('tipo')} - Sección {mesa.get('seccion')}")

print("\n" + "=" * 60)