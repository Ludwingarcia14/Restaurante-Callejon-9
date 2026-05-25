from flask import request
from controllers.auth.AuthController import AuthController
from controllers.dashboard.dashboard_controller import DashboardController


def register_auth_routes(bp):
    bp.add_url_rule("/", view_func=DashboardController.index, endpoint="home")
    bp.add_url_rule("/login", view_func=AuthController.login, methods=["GET", "POST"], endpoint="login")
    bp.add_url_rule("/logout", view_func=AuthController.logout, endpoint="logout")
    bp.add_url_rule("/verify-2fa", view_func=AuthController.verify_2fa, methods=["POST"], endpoint="verify_2fa")

    @bp.route('/api/2fa/emergency-disable')
    def api_2fa_emergency_disable():
        email = request.args.get('email', '')
        return AuthController.emergency_disable_2fa(email)
