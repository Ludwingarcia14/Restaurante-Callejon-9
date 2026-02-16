"""
Dashboard Controller - Sistema Restaurante Callejón 9
CORRECCIÓN: Agregado soporte para rol de inventario (4) en validación
"""
from flask import request, session, redirect, url_for, render_template, jsonify
from controllers.inventario.inventarioController import InventarioController
from models.empleado_model import Usuario, RolPermisos
from config.db import db
from bson.objectid import ObjectId
from datetime import datetime

class DashboardController:

    @staticmethod
    def home():
        """Renderiza login si no hay sesión"""
        return render_template("login.html")

    @staticmethod
    def index():
        """Redirige al dashboard según el rol del usuario"""
        if "usuario_rol" not in session:
            return redirect(url_for("routes.login"))

        rol = str(session["usuario_rol"])

        rol_endpoints = {
            "1": "dashboard_admin",
            "2": "dashboard_mesero",
            "3": "dashboard_cocina",
            "4": "dashboard_inventario"
        }

        endpoint = rol_endpoints.get(rol)
        print(f"Redirigiendo al endpoint: {endpoint} (Rol: {rol})")
        
        if endpoint:
            return redirect(url_for(f"routes.{endpoint}"))
        else:
            print(f" Rol no reconocido: {rol}")
            return "⚠ Rol no reconocido", 403

    # ==========================================
    # DASHBOARDS POR ROL
    # ==========================================

    @staticmethod
    def admin():
        """Dashboard principal de Administración (Rol 1)"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "1":
            return redirect(url_for("routes.login"))
        
        stats = {
            "total_usuarios": db.usuarios.count_documents({"usuario_status": 1}),
            "total_admin": db.usuarios.count_documents({"usuario_rol": "1"}),
            "total_meseros": db.usuarios.count_documents({"usuario_rol": "2"}),
            "total_cocina": db.usuarios.count_documents({"usuario_rol": "3"}),
            "total_inventario": db.usuarios.count_documents({"usuario_rol": "4"})
        }
        
        return render_template("admin/dashboard.html", 
                             usuario=session.get("usuario_nombre"),
                             rol_nombre=RolPermisos.get_nombre_rol("1"),
                             stats=stats)

    @staticmethod
    def mesero():
        """Dashboard principal de Mesero (Rol 2)"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "2":
            return redirect(url_for("routes.login"))
        
        perfil_mesero = session.get("perfil_mesero", {})
        comandas_activas = []
        
        stats = {
            "mesas_asignadas": perfil_mesero.get("mesas_asignadas", []),
            "comandas_activas": len(comandas_activas),
            "propinas_dia": perfil_mesero.get("propinas", {}).get("acumulada_dia", 0),
            "ventas_promedio": perfil_mesero.get("rendimiento", {}).get("ventas_promedio_dia", 0)
        }
        
        return render_template("mesero/dashboard.html",
                             usuario=session.get("usuario_nombre"),
                             rol_nombre=RolPermisos.get_nombre_rol("2"),
                             perfil=perfil_mesero,
                             comandas=comandas_activas,
                             stats=stats)

    @staticmethod
    def cocina():
        """Dashboard principal de Cocina (Rol 3)"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "3":
            return redirect(url_for("routes.login"))
        
        perfil_cocina = session.get("perfil_cocina", {})
        comandas_pendientes = []
        
        stats = {
            "area": perfil_cocina.get("area", "general"),
            "turno": perfil_cocina.get("turno", ""),
            "platillos_pendientes": 0,
            "especialidad": perfil_cocina.get("especialidad", [])
        }
        
        return render_template("cocina/dashboard.html",
                             usuario=session.get("usuario_nombre"),
                             rol_nombre=RolPermisos.get_nombre_rol("3"),
                             perfil=perfil_cocina,
                             comandas=comandas_pendientes,
                             stats=stats)
    @staticmethod
    def inventario():
        """Dashboard principal de Inventario (Rol 4)"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "4":
            return redirect(url_for("routes.login"))
    
        return InventarioController.dashboard()
    # ==========================================
    # GESTIÓN DE EMPLEADOS
    # ==========================================

    @staticmethod
    def empleados_lista():
        """Lista de empleados para administración"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "1":
            return redirect(url_for("routes.login"))
            
        empleados = Usuario.find_activos()
        
        for emp in empleados:
            emp["rol_nombre"] = RolPermisos.get_nombre_rol(emp.get("usuario_rol"))
        
        return render_template("admin/empleados/lista.html", empleados=empleados)

    @staticmethod
    def empleados_crear():
        """Formulario de creación de empleado"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "1":
            return redirect(url_for("routes.login"))
            
        if request.method == "POST":
            try:
                data = request.get_json()
                
                required_fields = ["nombre", "apellidos", "email", "password", "rol"]
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({
                            "success": False,
                            "message": f"El campo '{field}' es obligatorio"
                        }), 400
                
                if Usuario.find_by_email(data["email"]):
                    return jsonify({
                        "success": False,
                        "message": "Ya existe un empleado con este correo"
                    }), 400
                
                if data["rol"] not in ["1", "2", "3", "4"]:
                    return jsonify({
                        "success": False,
                        "message": "Rol no válido"
                    }), 400
                
                # Contraseña
                nuevo_empleado = {
                    "usuario_nombre": data["nombre"],
                    "usuario_apellidos": data["apellidos"],
                    "usuario_email": data["email"].lower(),
                    "usuario_clave": data["password"],
                    "usuario_rol": data["rol"],
                    "usuario_telefono": data.get("telefono", ""),
                    "usuario_foto": None,
                    "usuario_status": 1,
                    "usuario_tokensession": None,
                    "2fa_enabled": False,
                    "2fa_tipo": None,
                    "2fa_secret": None,
                    "2fa_telefono": None,
                    "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": datetime.utcnow()
                }
                
                if data["rol"] == "2":  # Mesero
                    nuevo_empleado.update({
                        "mesero_numero": data.get("numero_empleado", ""),
                        "mesero_turno": data.get("turno", ""),
                        "mesero_mesas": data.get("mesas_asignadas", []),
                        "mesero_puede_cerrar_cuenta": data.get("puede_cerrar_cuenta", False),
                        "mesero_puede_aplicar_descuento": data.get("puede_aplicar_descuento", False),
                        "mesero_propina_sugerida": 10,
                        "mesero_propina_acumulada_dia": 0,
                        "mesero_ventas_promedio_dia": 0,
                        "mesero_calificacion_cliente": 0
                    })
                elif data["rol"] == "3":  # Cocina
                    nuevo_empleado.update({
                        "cocina_numero": data.get("numero_empleado", ""),
                        "cocina_puesto": data.get("puesto", ""),
                        "cocina_area": data.get("area", "general"),
                        "cocina_turno": data.get("turno", ""),
                        "cocina_especialidad": data.get("especialidad", []),
                        "cocina_puede_modificar_menu": data.get("puede_modificar_menu", False),
                        "cocina_puede_ver_recetas_completas": data.get("puede_ver_recetas", False),
                        "cocina_certificaciones": data.get("certificaciones", [])
                    })
                elif data["rol"] == "4":  # Inventario
                    nuevo_empleado.update({
                        "inventario_numero": data.get("numero_empleado", ""),
                        "inventario_area": data.get("area", ""),
                        "inventario_turno": data.get("turno", ""),
                        "inventario_puede_gestionar_proveedores": data.get("puede_gestionar_proveedores", False),
                        "inventario_puede_realizar_auditorias": data.get("puede_realizar_auditorias", False)
                    })
                
                result = Usuario.create(nuevo_empleado)
                
                return jsonify({
                    "success": True,
                    "message": "Empleado creado exitosamente",
                    "id": str(result.inserted_id)
                })
                
            except Exception as e:
                print(f"Error al crear empleado: {e}")
                return jsonify({
                    "success": False,
                    "message": "Error al crear empleado"
                }), 500
        
        return render_template("admin/empleados/crear.html")

    @staticmethod
    def reportes():
        """Vista de reportes para administración"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "1":
            return redirect(url_for("routes.login"))
        return render_template("support/reportes/index.html")

    @staticmethod
    def toggle_theme():
        """Cambia el tema visual (light/dark)"""
        try:
            current_theme = session.get('theme', 'light')
            session['theme'] = 'dark' if current_theme == 'light' else 'light'
        except Exception as e:
            print(f"Error al cambiar tema: {e}")
        
        return redirect(request.referrer or url_for('routes.login'))

    @staticmethod
    def get_dashboard_stats():
        """Obtiene estadísticas reales del sistema para el dashboard"""
        from flask import jsonify
        from config.db import db
        from datetime import datetime, timedelta
        
        try:
            # Total de empleados
            total_empleados = db.usuarios.count_documents({
                "usuario_rol": {"$in": ["1", "2", "3", "4"]}
            })
            
            # Personal activo (status = 1)
            empleados_activos = db.usuarios.count_documents({
                "usuario_rol": {"$in": ["1", "2", "3", "4"]},
                "usuario_status": 1
            })
            
            # Por rol específico
            admin_count = db.usuarios.count_documents({"usuario_rol": "1"})
            meseros_count = db.usuarios.count_documents({"usuario_rol": "2"})
            cocina_count = db.usuarios.count_documents({"usuario_rol": "3"})
            inventario_count = db.usuarios.count_documents({"usuario_rol": "4"})
            
            # Mesas ocupadas
            mesas_ocupadas = 0
            try:
                if "mesas" in db.list_collection_names():
                    mesas_ocupadas = db.mesas.count_documents({"estado": "ocupada"})
            except:
                pass
            
            # Comandas activas
            comandas_activas = 0
            try:
                if "comandas" in db.list_collection_names():
                    comandas_activas = db.comandas.count_documents({
                        "estado": {"$in": ["nueva", "enviada", "preparacion"]}
                    })
            except:
                pass
            
            # Pedidos en cocina
            en_cocina = 0
            try:
                if "comandas" in db.list_collection_names():
                    en_cocina = db.comandas.count_documents({
                        "estado": {"$in": ["enviada", "preparacion"]}
                    })
            except:
                pass
            
            # Ventas del día
            hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            ventas_dia = 0
            
            try:
                if "ventas" in db.list_collection_names():
                    pipeline = [
                        {"$match": {
                            "fecha": {"$gte": hoy_inicio},
                            "estado": {"$ne": "cancelada"}
                        }},
                        {"$group": {
                            "_id": None,
                            "total": {"$sum": "$total"}
                        }}
                    ]
                    resultado = list(db.ventas.aggregate(pipeline))
                    if resultado:
                        ventas_dia = resultado[0].get("total", 0)
            except:
                pass
            
            # Cuentas abiertas
            cuentas_abiertas = 0
            try:
                if "cuentas" in db.list_collection_names():
                    cuentas_abiertas = db.cuentas.count_documents({
                        "estado": {"$in": ["abierta", "activa"]}
                    })
            except:
                pass
            
            # Platillos disponibles
            platillos_disponibles = 0
            try:
                if "menu" in db.list_collection_names():
                    platillos_disponibles = db.menu.count_documents({
                        "disponible": True
                    })
            except:
                pass
            
            return jsonify({
                "success": True,
                "data": {
                    "total_empleados": total_empleados,
                    "empleados_activos": empleados_activos,
                    "admin_count": admin_count,
                    "meseros_count": meseros_count,
                    "cocina_count": cocina_count,
                    "inventario_count": inventario_count,
                    "mesas_ocupadas": mesas_ocupadas,
                    "comandas_activas": comandas_activas,
                    "en_cocina": en_cocina,
                    "ventas_dia": float(ventas_dia),
                    "cuentas_abiertas": cuentas_abiertas,
                    "platillos_disponibles": platillos_disponibles,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500