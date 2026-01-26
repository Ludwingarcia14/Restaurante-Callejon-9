"""
Dashboard Controller - Sistema Restaurante Callejón 9
Adaptado a la estructura actual de roles: 1=Admin, 2=Mesero, 3=Cocina
"""
from flask import request, session, redirect, url_for, render_template
from models.empleado_model import Usuario, RolPermisos
from dotenv import load_dotenv
import os

load_dotenv()

SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY")
SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")

class DashboardController:

    @staticmethod
    def home():
        """Renderiza login si no hay sesión"""
        print(SITE_KEY)
        return render_template("login.html", site_key=SITE_KEY)

    @staticmethod
    def index():
        """Redirige al dashboard según el rol del usuario"""
        print(SITE_KEY)
        
        # Si no hay sesión, redirigir al login
        if "usuario_rol" not in session:
            return redirect(url_for("routes.login"))

        rol = str(session["usuario_rol"])

        # Mapeo de roles del restaurante
        rol_endpoints = {
            "1": "dashboard_admin",      # Administración
            "2": "dashboard_mesero",      # Mesero
            "3": "dashboard_cocina"       # Cocina
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
        
        from config.db import db
        
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
        
        from config.db import db
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
        
        from config.db import db
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
    # VISTAS ADICIONALES
    # ==========================================

    @staticmethod
    def reportes():
        """Vista de reportes para administración"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "1":
            return redirect(url_for("routes.login"))
        return render_template("admin/reportes/index.html")

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
            # Lógica de creación (delegada a Command Handler)
            pass
        return render_template("admin/empleados/crear.html")

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