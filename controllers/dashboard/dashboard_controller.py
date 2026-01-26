"""
Dashboard Controller - Sistema Restaurante Callejón 9
Roles: 1=Admin, 2=Mesero, 3=Cocina
"""
from flask import request, session, redirect, url_for, render_template, jsonify
from models.empleado_model import Usuario, RolPermisos
from config.db import db
from bson.objectid import ObjectId
import bcrypt
from datetime import datetime

class DashboardController:

    @staticmethod
    def home():
        """Renderiza login si no hay sesión"""
        return render_template("login.html")

    @staticmethod
    def index():
        """Redirige al dashboard según el rol del usuario"""
        # Si no hay sesión, redirigir al login
        if "usuario_rol" not in session:
            return redirect(url_for("routes.login"))

        rol = str(session["usuario_rol"])

        # Mapeo de roles del restaurante
        rol_endpoints = {
            "1": "dashboard_admin",    # Administración
            "2": "dashboard_mesero",    # Mesero
            "3": "dashboard_cocina"     # Cocina
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
        
        # Obtener estadísticas generales
        stats = {
            "total_usuarios": db.usuarios.count_documents({"usuario_status": 1}),
            "total_admin": db.usuarios.count_documents({"usuario_rol": "1"}),
            "total_meseros": db.usuarios.count_documents({"usuario_rol": "2"}),
            "total_cocina": db.usuarios.count_documents({"usuario_rol": "3"}),
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
        
        usuario_id = session.get("usuario_id")
        
        # Obtener perfil del mesero desde la sesión
        perfil_mesero = session.get("perfil_mesero", {})
        
        # Obtener comandas activas del mesero (simulado por ahora)
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
        
        usuario_id = session.get("usuario_id")
        
        # Obtener perfil de cocina desde la sesión
        perfil_cocina = session.get("perfil_cocina", {})
        
        # Obtener comandas activas para cocina (simulado)
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

    # ==========================================
    # GESTIÓN DE EMPLEADOS (SOLO ADMIN)
    # ==========================================

    @staticmethod
    def empleados_lista():
        """Lista de empleados para administración"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "1":
            return redirect(url_for("routes.login"))
            
        empleados = Usuario.find_activos()
        
        # Enriquecer con nombres de roles
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
                
                # Validaciones
                required_fields = ["nombre", "apellidos", "email", "password", "rol"]
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({
                            "success": False,
                            "message": f"El campo '{field}' es obligatorio"
                        }), 400
                
                # Verificar que el email no exista
                if Usuario.find_by_email(data["email"]):
                    return jsonify({
                        "success": False,
                        "message": "Ya existe un empleado con este correo"
                    }), 400
                
                # Validar que el rol sea válido (1, 2 o 3)
                if data["rol"] not in ["1", "2", "3"]:
                    return jsonify({
                        "success": False,
                        "message": "Rol no válido"
                    }), 400
                
                # Hashear contraseña
                salt = bcrypt.gensalt(rounds=12)
                hashed_password = bcrypt.hashpw(
                    data["password"].encode("utf-8"), 
                    salt
                ).decode("utf-8")
                
                # Preparar datos del nuevo empleado
                nuevo_empleado = {
                    "usuario_nombre": data["nombre"],
                    "usuario_apellidos": data["apellidos"],
                    "usuario_email": data["email"].lower(),
                    "usuario_clave": hashed_password,
                    "usuario_rol": data["rol"],
                    "usuario_telefono": data.get("telefono", ""),
                    "usuario_foto": None,
                    "usuario_status": 1,  # Activo por defecto
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
                
                # Insertar en BD
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
        
        # GET - Mostrar formulario
        return render_template("admin/empleados/crear.html")

    # ==========================================
    # UTILIDADES
    # ==========================================

    @staticmethod
    def reportes():
        """Vista de reportes para administración"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "1":
            return redirect(url_for("routes.login"))
        return render_template("admin/reportes/index.html")

    @staticmethod
    def toggle_theme():
        """Cambia el tema visual (light/dark)"""
        try:
            current_theme = session.get('theme', 'light')
            
            if current_theme == 'light':
                session['theme'] = 'dark'
            else:
                session['theme'] = 'light'
                
        except Exception as e:
            print(f"Error al cambiar tema: {e}")
            pass

        # Redirige al usuario de vuelta a la página donde estaba
        return redirect(request.referrer or url_for('routes.login'))