from . import routes_bp
from controllers.auth.AuthController import AuthController
from controllers.dashboard.dashboard_controller import DashboardController
from extensions import limiter

# Raíz
@routes_bp.route("/")
def home():
    return DashboardController.index()

# Login / Logout
_login_view = limiter.limit("10 per minute")(AuthController.login)
routes_bp.add_url_rule("/login", view_func=_login_view, methods=["GET", "POST"], endpoint="login")
routes_bp.add_url_rule("/logout", view_func=AuthController.logout, endpoint="logout")
routes_bp.add_url_rule("/verify-2fa", view_func=AuthController.verify_2fa, methods=["POST"], endpoint="verify_2fa")
