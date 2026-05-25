from controllers.auth.AuthController import login_required
from controllers.settings.settingsController import SettingsController


def register_settings_routes(bp):

    @bp.route("/settings")
    @login_required
    def settings():
        return SettingsController.settings()

    @bp.route('/api/usuario/telefono', methods=['GET'])
    @login_required
    def api_usuario_telefono():
        return SettingsController.get_telefono()

    @bp.route('/api/usuario/actualizar', methods=['POST'])
    @login_required
    def api_usuario_actualizar():
        return SettingsController.actualizar_perfil()

    @bp.route('/api/2fa/setup', methods=['POST'])
    @login_required
    def api_2fa_setup():
        return SettingsController.generate_2fa_setup()

    @bp.route('/api/2fa/verify', methods=['POST'])
    @login_required
    def api_2fa_verify():
        return SettingsController.verify_and_enable_2fa()

    @bp.route('/api/2fa/disable', methods=['POST'])
    @login_required
    def api_2fa_disable():
        return SettingsController.disable_2fa()
