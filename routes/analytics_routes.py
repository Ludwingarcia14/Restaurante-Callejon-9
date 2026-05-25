from controllers.auth.AuthController import login_required, rol_required
from controllers.analytics.analytics_controller import AnalyticsController


def register_analytics_routes(bp):

    @bp.route("/admin/analytics")
    @login_required
    @rol_required(['1'])
    def analytics_index():
        return AnalyticsController.index()

    @bp.route("/api/analytics/kpis")
    @login_required
    @rol_required(['1'])
    def api_analytics_kpis():
        return AnalyticsController.get_kpis()

    @bp.route("/api/analytics/top-platillos")
    @login_required
    @rol_required(['1'])
    def api_analytics_top_platillos():
        return AnalyticsController.get_top_platillos()

    @bp.route("/api/analytics/ventas-por-dia")
    @login_required
    @rol_required(['1'])
    def api_analytics_ventas_dia():
        return AnalyticsController.get_ventas_por_dia()

    @bp.route("/api/analytics/metodos-pago")
    @login_required
    @rol_required(['1'])
    def api_analytics_metodos_pago():
        return AnalyticsController.get_ventas_por_metodo_pago()

    @bp.route("/api/analytics/horas-pico")
    @login_required
    @rol_required(['1'])
    def api_analytics_horas_pico():
        return AnalyticsController.get_horas_pico()

    @bp.route("/api/analytics/rendimiento-meseros")
    @login_required
    @rol_required(['1'])
    def api_analytics_meseros():
        return AnalyticsController.get_rendimiento_meseros()

    @bp.route("/api/analytics/ventas-por-mesa")
    @login_required
    @rol_required(['1'])
    def api_analytics_ventas_mesa():
        return AnalyticsController.get_ventas_por_mesa()
