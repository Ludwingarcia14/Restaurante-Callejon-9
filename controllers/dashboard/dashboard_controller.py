from flask import request, session, redirect, url_for, render_template
from dotenv import load_dotenv
import os

SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY")
SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")

class DashboardController:

    @staticmethod
    def home():
        print(SITE_KEY)
        """ Renderiza login si no hay sesión """
        return render_template("login.html", site_key=SITE_KEY)  # Ajustado a tu estructura
    
    @staticmethod
    def loginClient():
        if "usuario_rol" not in session:
            return render_template("login_client.html", site_key=SITE_KEY)  # Ajustado a tu estructura

    @staticmethod
    def retrievepassword():
        if "usuario_rol" not in session:
            return render_template("auth/retrievepassword.html")  # Ajustado a tu estructura

    @staticmethod
    def registerClient():
        if "usuario_rol" not in session:
            return render_template("auth/register_client.html")  # Ajustado a tu estructura

    @staticmethod
    def index():
        """ Redirige al dashboard según el rol del usuario """
        print(SITE_KEY)
        if "usuario_rol" not in session:
            return render_template("login.html")

        rol = str(session["usuario_rol"])

        # Mapeo explícito de rol → endpoint
        rol_endpoints = {
            "1": "dashboard_Sadmin",
            "2": "dashboard_admin",
            "3": "dashboard_asesor",
            "4": "dashboard_client",
            "5": "dashboard_financiera",
            "6": "dashboard_soporte"
        }

        endpoint = rol_endpoints.get(rol)
        print(f"Redirigiendo al endpoint: {endpoint}")  # Depuración
        if endpoint:
            # Añadir nombre del blueprint antes del endpoint
            return redirect(url_for(f"routes.{endpoint}", site_key=SITE_KEY))
        else:
            return "⚠ Rol no reconocido"

    @staticmethod
    def admin():
        if "usuario_rol" in session and str(session["usuario_rol"]) == "1":
            return render_template("admin/dashboard.html", usuario=session.get("usuario_nombre"))
        return redirect(url_for("routes.login"))

    @staticmethod
    def client():
        if "usuario_rol" in session and str(session["usuario_rol"]) == "2":
            return render_template("client/dashboard.html", usuario=session.get("usuario_nombre"))
        return redirect(url_for("routes.login"))

    @staticmethod
    def financiera():
        if "usuario_rol" in session and str(session["usuario_rol"]) == "3":
            return render_template("financiera/dashboard.html", usuario=session.get("usuario_nombre"))
        return redirect(url_for("routes.login"))
    
    @staticmethod
    def DashboardClient(): 
        if "usuario_rol" in session and str(session["usuario_rol"]) == "4":
            return render_template("client/dashboard.html", usuario=session.get("usuario_nombre"))
        return redirect(url_for("routes.login"))
    
    @staticmethod
    def Dashboardsoporte(): 
        if "usuario_rol" in session and str(session["usuario_rol"]) == "6":
            return render_template("support/dashboard.html", usuario=session.get("usuario_nombre"))
        return redirect(url_for("routes.login"))
    
    @staticmethod
    def DashboardAsesor():
        if "usuario_rol" in session and str(session["usuario_rol"]) == "5":
            return render_template("financiera/dashboard.html", usuario=session.get("usuario_nombre"))
        return redirect(url_for("routes.login"))

    
    def toggle_theme():
        """
        Cambia el tema en la sesión entre 'light' y 'dark'.
        """
        try:
            # Obtiene el tema actual, si no existe, asume 'light'
            current_theme = session.get('theme', 'light')
            
            # Cambia al tema opuesto
            if current_theme == 'light':
                session['theme'] = 'dark'
            else:
                session['theme'] = 'light'
                
        except Exception as e:
            # En caso de error, simplemente no hagas nada
            print(f"Error al cambiar tema: {e}")
            pass

        # Redirige al usuario de vuelta a la página donde estaba
        # request.referrer es la URL de la página anterior
        return redirect(request.referrer or url_for('routes.login2'))