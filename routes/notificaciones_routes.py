from controllers.auth.AuthController import login_required
from controllers.notificaciones.notificacion_controller import NotificacionController


def register_notificaciones_routes(bp):

    @bp.route('/api/me', methods=['GET'])
    @login_required
    def api_me():
        return NotificacionController.get_datos_socket()

    @bp.route('/api/notificaciones', methods=['GET'])
    @login_required
    def api_notificaciones():
        return NotificacionController.get_notificaciones()

    @bp.route('/api/notificaciones/no-leidas', methods=['GET'])
    @login_required
    def api_notificaciones_no_leidas():
        return NotificacionController.get_notificaciones_no_leidas()

    @bp.route('/api/notificaciones/contador', methods=['GET'])
    @login_required
    def api_notificaciones_contador():
        return NotificacionController.get_contador()

    @bp.route('/api/notificaciones/<id_notificacion>/leida', methods=['PUT'])
    @login_required
    def api_notificacion_leida(id_notificacion):
        return NotificacionController.marcar_leida(id_notificacion)

    @bp.route('/api/notificaciones/marcar-todas-leidas', methods=['POST'])
    @login_required
    def api_marcar_todas_leidas():
        return NotificacionController.marcar_todas_leidas()

    @bp.route('/api/notificaciones/<id_notificacion>', methods=['DELETE'])
    @login_required
    def api_eliminar_notificacion(id_notificacion):
        return NotificacionController.eliminar_notificacion(id_notificacion)
