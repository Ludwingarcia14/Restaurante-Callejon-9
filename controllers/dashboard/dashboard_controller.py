"""
Dashboard Controller - Sistema Restaurante Callejón 9
Versión simplificada sin bcrypt para desarrollo local
Roles: 1=Admin, 2=Mesero, 3=Cocina
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
            "3": "dashboard_cocina"
        }

        endpoint = rol_endpoints.get(rol)
        print(f"🔄 Redirigiendo al endpoint: {endpoint} (Rol: {rol})")
        
        if endpoint:
            return redirect(url_for(f"routes.{endpoint}"))
        else:
            print(f"❌ Rol no reconocido: {rol}")
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
    # GESTIÓN DE EMPLEADOS (SOLO ADMIN)
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
                
                if data["rol"] not in ["1", "2", "3"]:
                    return jsonify({
                        "success": False,
                        "message": "Rol no válido"
                    }), 400
                
                # Contraseña en texto plano
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
                
                # Campos específicos por rol
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
"""
API Controller para Dashboard de Administración
Proporciona endpoints para obtener datos en tiempo real
"""
from flask import jsonify, session
from config.db import db
from datetime import datetime, timedelta
from bson import ObjectId

class DashboardAPIController:
    
    @staticmethod
    def get_stats():
        """Obtiene estadísticas generales del dashboard"""
        try:
            if "usuario_rol" not in session or str(session["usuario_rol"]) != "1":
                return jsonify({"error": "No autorizado"}), 403
            
            hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            total_empleados = db.usuarios.count_documents({"usuario_rol": {"$in": ["1", "2", "3", "4"]}})
            empleados_activos = db.usuarios.count_documents({
                "usuario_rol": {"$in": ["1", "2", "3", "4"]},
                "usuario_status": 1
            })
            
            total_mesas = db.mesas.count_documents({"activa": True})
            mesas_ocupadas = db.mesas.count_documents({"estado": "ocupada", "activa": True})
            
            comandas_activas = db.comandas.count_documents({
                "estado": {"$in": ["nueva", "en_cocina", "preparando"]}
            })
            
            comandas_listas = db.comandas.count_documents({"estado": "lista"})
            
            ventas_hoy = list(db.ventas.aggregate([
                {
                    "$match": {
                        "fecha": {"$gte": hoy_inicio}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$total"},
                        "cantidad": {"$sum": 1}
                    }
                }
            ]))
            
            ventas_dia = float(ventas_hoy[0]["total"]) if ventas_hoy else 0
            num_ventas = ventas_hoy[0]["cantidad"] if ventas_hoy else 0
            
            total_platillos = db.platillos.count_documents({"disponible": True})
            
            stats = {
                "total_empleados": total_empleados,
                "empleados_activos": empleados_activos,
                "total_admin": db.usuarios.count_documents({"usuario_rol": "1"}),
                "total_meseros": db.usuarios.count_documents({"usuario_rol": "2"}),
                "total_cocina": db.usuarios.count_documents({"usuario_rol": "3"}),
                "total_inventario": db.usuarios.count_documents({"usuario_rol": "4"}),
                "mesas_ocupadas": mesas_ocupadas,
                "mesas_disponibles": total_mesas - mesas_ocupadas,
                "comandas_activas": comandas_activas,
                "comandas_listas": comandas_listas,
                "ventas_dia": ventas_dia,
                "num_ventas": num_ventas,
                "total_platillos": total_platillos,
                "en_cocina": db.comandas.count_documents({"estado": "en_cocina"})
            }
            
            return jsonify(stats)
            
        except Exception as e:
            print(f"Error en get_stats: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    
    @staticmethod
    def get_actividad_reciente():
        """Obtiene las últimas actividades del sistema"""
        try:
            if "usuario_rol" not in session or str(session["usuario_rol"]) != "1":
                return jsonify({"error": "No autorizado"}), 403
            
            actividades = list(db.actividad_reciente.find().sort("timestamp", -1).limit(10))
            
            for act in actividades:
                act["_id"] = str(act["_id"])
                if "usuario_id" in act:
                    act["usuario_id"] = str(act["usuario_id"])
                if "timestamp" in act and isinstance(act["timestamp"], datetime):
                    act["timestamp"] = act["timestamp"].isoformat()
            
            return jsonify(actividades)
            
        except Exception as e:
            print(f"Error en get_actividad_reciente: {e}")
            return jsonify({"error": str(e)}), 500
    
    @staticmethod
    def get_personal_activo():
        """Obtiene lista de personal actualmente conectado"""
        try:
            if "usuario_rol" not in session or str(session["usuario_rol"]) != "1":
                return jsonify({"error": "No autorizado"}), 403
            
            personal = list(db.usuarios.find({
                "usuario_rol": {"$in": ["1", "2", "3", "4"]},
                "usuario_status": 1
            }).sort("usuario_nombre", 1))
            
            resultado = []
            for p in personal:
                resultado.append({
                    "nombre": f"{p.get('usuario_nombre', '')} {p.get('usuario_apellidos', '')}".strip(),
                    "rol": p.get("usuario_rol", ""),
                    "email": p.get("usuario_email", ""),
                    "status": "online",
                    "ultimaActividad": "Hace 1 min"
                })
            
            return jsonify(resultado)
            
        except Exception as e:
            print(f"Error en get_personal_activo: {e}")
            return jsonify({"error": str(e)}), 500