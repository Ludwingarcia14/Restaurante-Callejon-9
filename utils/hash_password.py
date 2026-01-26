#!/usr/bin/env python3
"""
Script para generar hashes de contraseñas con bcrypt
Uso: python utils/hash_password.py
"""
import bcrypt

def hash_password(password):
    """Genera el hash bcrypt de una contraseña"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password, hashed):
    """Verifica si una contraseña coincide con su hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

if __name__ == "__main__":
    print("=" * 60)
    print("🔐 GENERADOR DE CONTRASEÑAS HASHEADAS")
    print("=" * 60)
    
    password = input("\n✏️  Introduce la contraseña a hashear: ")
    
    if not password:
        print("❌ La contraseña no puede estar vacía")
        exit(1)
    
    hashed = hash_password(password)
    
    print("\n✅ Hash generado:")
    print(f"   {hashed}")
    
    print("\n🔍 Verificando...")
    if verify_password(password, hashed):
        print("   ✅ La contraseña coincide con el hash")
    else:
        print("   ❌ Error en la verificación")
    
    print("\n📋 Copia este hash a tu base de datos MongoDB:")
    print(f'   "usuario_clave": "{hashed}"')
    print("=" * 60)