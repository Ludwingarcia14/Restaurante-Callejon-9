"""
Script de Prueba - Sistema de Notificaciones
Ejecutar este script para probar el sistema de notificaciones

Uso:
    python test_notificaciones.py
"""

import sys
import os
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def test_modelo_notificacion():
    """Prueba el modelo de Notificación"""
    print("\n" + "="*60)
    print("TEST 1: Modelo de Notificación")
    print("="*60)
    
    try:
        from models.notificacion import Notificacion
        from bson import ObjectId
        
        # Crear ID de prueba
        usuario_id = ObjectId()
        
        # Crear notificación
        nueva_notif = {
            "tipo": "LOGIN",
            "mensaje": "Usuario de prueba ha iniciado sesión",
            "id_usuario": usuario_id,
            "leida": False
        }
        
        result = Notificacion.create(nueva_notif)
        print(f"✅ Notificación creada con ID: {result.inserted_id}")
        
        # Obtener notificación
        notif = Notificacion.find_by_id(result.inserted_id)
        print(f"✅ Notificación recuperada: {notif['mensaje']}")
        
        # Limpiar
        Notificacion.delete(result.inserted_id)
        print("✅ Notificación eliminada (cleanup)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de modelo: {str(e)}")
        return False


def test_notificacion_handler():
    """Prueba el handler de comandos"""
    print("\n" + "="*60)
    print("TEST 2: Handler de Comandos")
    print("="*60)
    
    try:
        from cqrs.commands.handlers.notificacion_handler import NotificacionCommandHandler
        from bson import ObjectId
        
        # Crear ID de prueba
        usuario_id = str(ObjectId())
        
        # Crear notificación
        result = NotificacionCommandHandler.crear_notificacion(
            tipo="BACKUP_CREADO",
            mensaje="Backup de prueba creado exitosamente",
            id_usuario=usuario_id,
            datos_extra={"archivo": "test_backup.json"}
        )
        
        if result["success"]:
            print(f"✅ Notificación creada: {result['mensaje']}")
            
            # Marcar como leída
            result_leida = NotificacionCommandHandler.marcar_como_leida(result["id"])
            print(f"✅ Notificación marcada como leída: {result_leida['success']}")
            
            # Limpiar
            NotificacionCommandHandler.eliminar_notificacion(result["id"])
            print("✅ Notificación eliminada (cleanup)")
            
            return True
        else:
            print(f"❌ Error creando notificación: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de handler: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_notificacion_sistema():
    """Prueba las notificaciones del sistema según rol"""
    print("\n" + "="*60)
    print("TEST 3: Notificaciones del Sistema")
    print("="*60)
    
    try:
        from cqrs.commands.handlers.notificacion_handler import NotificacionSistemaHandler
        from bson import ObjectId
        
        # IDs de prueba
        admin_id = str(ObjectId())
        mesero_id = str(ObjectId())
        cocina_id = str(ObjectId())
        inventario_id = str(ObjectId())
        
        # Probar notificación de login
        result = NotificacionSistemaHandler.notificar_login(
            id_usuario=admin_id,
            nombre_usuario="Admin Test",
            rol="1"
        )
        print(f"✅ Notificación LOGIN (Admin): {result['success']}")
        
        # Probar notificación de backup
        result = NotificacionSistemaHandler.notificar_backup(
            id_usuario=admin_id,
            tipo_backup="crear",
            nombre_archivo="backup_test.json"
        )
        print(f"✅ Notificación BACKUP: {result['success']}")
        
        # Probar notificación de inventario
        result = NotificacionSistemaHandler.notificar_inventario(
            id_usuario=inventario_id,
            tipo_movimiento="entrada",
            nombre_insumo="Tomate",
            cantidad=50
        )
        print(f"✅ Notificación INVENTARIO: {result['success']}")
        
        # Probar notificación de error
        result = NotificacionSistemaHandler.notificar_error(
            id_usuario=admin_id,
            tipo_error="TEST_ERROR",
            descripcion="Este es un error de prueba"
        )
        print(f"✅ Notificación ERROR: {result['success']}")
        
        print("\n✅ Limpiando notificaciones de prueba...")
        from models.notificacion import Notificacion
        Notificacion.collection.delete_many({
            "id_usuario": {"$in": [
                ObjectId(admin_id),
                ObjectId(mesero_id),
                ObjectId(cocina_id),
                ObjectId(inventario_id)
            ]}
        })
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de sistema: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_query_handler():
    """Prueba el handler de queries"""
    print("\n" + "="*60)
    print("TEST 4: Query Handler")
    print("="*60)
    
    try:
        from cqrs.queries.handlers.notificacion_query_handler import NotificacionQueryHandler
        from models.notificacion import Notificacion
        from bson import ObjectId
        
        # Crear ID de prueba
        usuario_id = ObjectId()
        
        # Crear algunas notificaciones de prueba
        for i in range(3):
            Notificacion.create({
                "tipo": f"TEST_{i}",
                "mensaje": f"Notificación de prueba {i}",
                "id_usuario": usuario_id,
                "leida": False
            })
        
        # Obtener notificaciones
        notificaciones = NotificacionQueryHandler.get_notificaciones(
            id_usuario_str=str(usuario_id),
            Notificacion_Model=Notificacion.collection
        )
        
        print(f"✅ Se obtuvieron {len(notificaciones)} notificaciones")
        
        for notif in notificaciones:
            print(f"   - {notif['tipo']}: {notif['mensaje']}")
        
        # Limpiar
        Notificacion.collection.delete_many({"id_usuario": usuario_id})
        print("✅ Notificaciones de prueba eliminadas (cleanup)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de query: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_servicio_notificacion():
    """Prueba el servicio de notificación (Socket.IO)"""
    print("\n" + "="*60)
    print("TEST 5: Servicio de Notificación Socket.IO")
    print("="*60)
    
    try:
        from services.notificaciones.notification_service import notificar_usuario
        from bson import ObjectId
        
        usuario_id = str(ObjectId())
        
        # Intentar enviar notificación
        result = notificar_usuario(
            user_id=usuario_id,
            evento="TEST_SOCKET",
            mensaje="Prueba de Socket.IO",
            datos_extra={"test": True}
        )
        
        if result:
            print("✅ Notificación enviada correctamente al servicio Socket.IO")
        else:
            print("⚠️ Usuario no conectado (esperado en prueba)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de servicio: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "="*60)
    print("SISTEMA DE PRUEBAS - NOTIFICACIONES")
    print("Restaurante Callejón 9")
    print("="*60)
    
    # Verificar conexión a MongoDB
    try:
        from config.db import db
        db.command('ping')
        print("✅ Conexión a MongoDB exitosa")
    except Exception as e:
        print(f"❌ Error de conexión a MongoDB: {str(e)}")
        print("Verifica que MongoDB esté corriendo y la configuración sea correcta")
        return
    
    # Lista de pruebas
    pruebas = [
        ("Modelo de Notificación", test_modelo_notificacion),
        ("Handler de Comandos", test_notificacion_handler),
        ("Notificaciones del Sistema", test_notificacion_sistema),
        ("Query Handler", test_query_handler),
        ("Servicio Socket.IO", test_servicio_notificacion)
    ]
    
    resultados = []
    
    # Ejecutar pruebas
    for nombre, test_func in pruebas:
        try:
            resultado = test_func()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"\n❌ Error ejecutando {nombre}: {str(e)}")
            import traceback
            traceback.print_exc()
            resultados.append((nombre, False))
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    
    exitosas = sum(1 for _, r in resultados if r)
    total = len(resultados)
    
    for nombre, resultado in resultados:
        status = "✅ PASÓ" if resultado else "❌ FALLÓ"
        print(f"{status} - {nombre}")
    
    print("\n" + "="*60)
    print(f"Resultado: {exitosas}/{total} pruebas exitosas")
    print("="*60)
    
    if exitosas == total:
        print("\n🎉 ¡Todas las pruebas pasaron! El sistema está listo.")
    else:
        print("\n⚠️ Algunas pruebas fallaron. Revisar los errores arriba.")


if __name__ == "__main__":
    main()