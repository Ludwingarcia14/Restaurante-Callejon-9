from . import routes_bp
from controllers.auth.AuthController import login_required
from controllers.dashboard.dashboard_controller import DashboardController
from controllers.dashboard.dashboardApiController import DashboardAPIController
from controllers.settings.settingsController import SettingsController

@routes_bp.route("/settings")
@login_required
def settings():
    return SettingsController.settings()

@routes_bp.route('/api/usuario/telefono', methods=['GET'])
@login_required
def api_usuario_telefono():
    return SettingsController.get_telefono()

@routes_bp.route('/api/usuario/actualizar', methods=['POST'])
@login_required
def api_usuario_actualizar():
    return SettingsController.actualizar_perfil()

@routes_bp.route('/api/2fa/setup', methods=['POST'])
@login_required
def api_2fa_setup():
    return SettingsController.generate_2fa_setup()

@routes_bp.route('/api/2fa/verify', methods=['POST'])
@login_required
def api_2fa_verify():
    return SettingsController.verify_and_enable_2fa()

@routes_bp.route('/api/2fa/disable', methods=['POST'])
@login_required
def api_2fa_disable():
    return SettingsController.disable_2fa()

@routes_bp.route("/toggle-theme", methods=["GET", "POST"])
def toggle_theme():
    return DashboardController.toggle_theme()

@routes_bp.route('/api/settings/sistema', methods=['GET'])
def api_settings_get():
    return DashboardAPIController.get_settings()

@routes_bp.route('/api/settings/sistema', methods=['POST'])
def api_settings_update():
    return DashboardAPIController.update_settings()
