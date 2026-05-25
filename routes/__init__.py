from flask import Blueprint

routes_bp = Blueprint("routes", __name__)

from .auth_routes import register_auth_routes
from .notificaciones_routes import register_notificaciones_routes
from .settings_routes import register_settings_routes
from .admin_routes import register_admin_routes
from .mesero_routes import register_mesero_routes
from .cocina_routes import register_cocina_routes
from .inventario_routes import register_inventario_routes
from .ventas_routes import register_ventas_routes
from .analytics_routes import register_analytics_routes
from .backup_routes import register_backup_routes
from .pago_routes import register_pago_routes

register_auth_routes(routes_bp)
register_notificaciones_routes(routes_bp)
register_settings_routes(routes_bp)
register_admin_routes(routes_bp)
register_mesero_routes(routes_bp)
register_cocina_routes(routes_bp)
register_inventario_routes(routes_bp)
register_ventas_routes(routes_bp)
register_analytics_routes(routes_bp)
register_backup_routes(routes_bp)
register_pago_routes(routes_bp)


def register_reports_routes(app):
    from controllers.reports.reports_controller import reports_bp
    app.register_blueprint(reports_bp)
