from . import routes_bp
from flask import request
from controllers.auth.AuthController import AuthController
from controllers.dashboard.dashboard_controller import DashboardController
from extensions import limiter

@routes_bp.route("/")
def home():
    return DashboardController.index()

_login_view = limiter.limit("10 per minute", methods=["POST"])(AuthController.login)
routes_bp.add_url_rule("/login", view_func=_login_view, methods=["GET", "POST"], endpoint="login")
routes_bp.add_url_rule("/logout", view_func=AuthController.logout, endpoint="logout")
routes_bp.add_url_rule("/verify-2fa", view_func=AuthController.verify_2fa, methods=["POST"], endpoint="verify_2fa")
routes_bp.add_url_rule("/api/heartbeat", view_func=AuthController.heartbeat, methods=["POST"], endpoint="heartbeat")

@routes_bp.route('/api/2fa/emergency-disable')
def api_2fa_emergency_disable():
    email = request.args.get('email', '')
    return AuthController.emergency_disable_2fa(email)
