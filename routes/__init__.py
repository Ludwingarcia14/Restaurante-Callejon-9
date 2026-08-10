"""
Rutas del sistema - Callejón 9
Separadas por módulo para mantener orden y claridad.
"""
from flask import Blueprint

routes_bp = Blueprint("routes", __name__)

from . import auth_routes          # noqa: F401, E402
from . import admin_routes         # noqa: F401, E402
from . import mesero_routes        # noqa: F401, E402
from . import cocina_routes        # noqa: F401, E402
from . import inventario_routes    # noqa: F401, E402
from . import ventas_routes        # noqa: F401, E402
from . import notificaciones_routes # noqa: F401, E402
from . import settings_routes      # noqa: F401, E402
from . import pagos_routes         # noqa: F401, E402
from . import analytics_routes     # noqa: F401, E402
from . import repartidor_routes    # noqa: F401, E402
from . import cliente_routes       # noqa: F401, E402

def register_reports_routes(app):
    from controllers.reports.reports_controller import reports_bp
    app.register_blueprint(reports_bp)
