from . import routes_bp
from flask import session, redirect, url_for, render_template, jsonify, request
from datetime import datetime
from controllers.auth.AuthController import login_required, rol_required
from controllers.dashboard.dashboard_controller import DashboardController
from controllers.historial.historialController import HistorialController
from controllers.comanda.comandaController import ComandaController
from controllers.mesa.mesaController import MesaController
from controllers.propina.propinasController import PropinasController
from controllers.mesero.kmeans_controller import MeseroKMeansController
from controllers.mesero.randomforest_controller import MeseroRandomForestController
from controllers.mesero.diagnostico_controller import MeseroDiagnosticoController
from controllers.mesero.metodologia_controller import MeseroMetodologiaController
from controllers.mesero.etl_controller import MeseroProcesosDatosController
from controllers.analytics.analytics_controller import AnalyticsController
from services.analytics_charts_service import AnalyticsChartsService
from models.producto_model import Producto

# ── Vistas ────────────────────────────────────────────────
@routes_bp.route("/dashboard/mesero")
@login_required
@rol_required(['2'])
def dashboard_mesero():
    return DashboardController.mesero()

@routes_bp.route("/mesero/mesas")
@login_required
@rol_required(['2'])
def mesero_mesas():
    return redirect(url_for("routes.dashboard_mesero"))

@routes_bp.route("/mesero/comandas")
@login_required
@rol_required(['2'])
def mesero_comandas():
    perfil_mesero = session.get("perfil_mesero")
    if not perfil_mesero:
        return redirect(url_for("routes.login"))
    return render_template("mesero/comandas.html", perfil=perfil_mesero,
                           stats={"mesas_asignadas": perfil_mesero.get("mesas_asignadas", [])})

@routes_bp.route("/mesero/menu")
@login_required
@rol_required(['2'])
def mesero_menu():
    perfil_mesero = session.get("perfil_mesero")
    if not perfil_mesero:
        return redirect(url_for("routes.login"))
    return render_template("mesero/mesero_menu.html", perfil=perfil_mesero,
                           stats={"mesas_asignadas": perfil_mesero.get("mesas_asignadas", [])})

@routes_bp.route("/mesero/propinas")
@login_required
@rol_required(['2'])
def mesero_propinas():
    perfil_mesero = session.get("perfil_mesero")
    if not perfil_mesero:
        return redirect(url_for("routes.login"))
    return render_template("mesero/mesero_propinas.html", perfil=perfil_mesero)

@routes_bp.route("/mesero/historial")
@login_required
@rol_required(['2'])
def mesero_historial():
    perfil_mesero = session.get("perfil_mesero")
    if not perfil_mesero:
        return redirect(url_for("routes.login"))
    return render_template("mesero/mesero_historial.html", perfil=perfil_mesero)

@routes_bp.route("/mesero/kmeans")
@login_required
@rol_required(['2'])
def mesero_kmeans():
    return MeseroKMeansController.vista()

@routes_bp.route("/mesero/arbol")
@login_required
@rol_required(['2'])
def mesero_arbol():
    return MeseroRandomForestController.vista()

@routes_bp.route("/mesero/diagnostico")
@login_required
@rol_required(['2'])
def mesero_diagnostico():
    return MeseroDiagnosticoController.vista()

@routes_bp.route("/mesero/metodologia")
@login_required
@rol_required(['2'])
def mesero_metodologia():
    return MeseroMetodologiaController.vista()

@routes_bp.route("/mesero/etl")
@login_required
@rol_required(['2'])
def mesero_etl():
    return MeseroProcesosDatosController.vista()

@routes_bp.route("/mesero/pareto")
@login_required
@rol_required(['2'])
def mesero_pareto():
    from flask import render_template as _rt
    return _rt("mesero/mesero_pareto.html", perfil=session.get("perfil_mesero", {}))

@routes_bp.route("/mesero/asociacion")
@login_required
@rol_required(['2'])
def mesero_asociacion():
    from flask import render_template as _rt
    return _rt("mesero/mesero_asociacion.html", perfil=session.get("perfil_mesero", {}))

@routes_bp.route("/mesero/prediccion")
@login_required
@rol_required(['2'])
def mesero_prediccion():
    from flask import render_template as _rt
    return _rt("mesero/mesero_prediccion.html", perfil=session.get("perfil_mesero", {}))

@routes_bp.route("/mesero/configuracion")
@login_required
@rol_required(['2'])
def mesero_config():
    perfil_mesero = session.get("perfil_mesero")
    if not perfil_mesero:
        return redirect(url_for("routes.login"))
    return render_template("mesero/config/config.html", perfil=perfil_mesero)

@routes_bp.route("/mesero/analitica")
@login_required
@rol_required(['2'])
def mesero_analitica():
    return render_template("mesero/mesero_analitica.html", perfil=session.get("perfil_mesero", {}))

@routes_bp.route("/mesero/tendencias")
@login_required
@rol_required(['2'])
def mesero_tendencias():
    return render_template("mesero/mesero_tendencias.html", perfil=session.get("perfil_mesero", {}))

@routes_bp.route("/mesero/histograma")
@login_required
@rol_required(['2'])
def mesero_histograma():
    return render_template("mesero/mesero_histograma.html", perfil=session.get("perfil_mesero", {}))

@routes_bp.route("/mesero/heatmap")
@login_required
@rol_required(['2'])
def mesero_heatmap():
    return render_template("mesero/mesero_heatmap.html", perfil=session.get("perfil_mesero", {}))

@routes_bp.route("/mesero/area")
@login_required
@rol_required(['2'])
def mesero_area():
    return render_template("mesero/mesero_area.html", perfil=session.get("perfil_mesero", {}))

@routes_bp.route("/mesero/boxplot")
@login_required
@rol_required(['2'])
def mesero_boxplot():
    return render_template("mesero/mesero_boxplot.html", perfil=session.get("perfil_mesero", {}))

# ── API Mesero ────────────────────────────────────────────
@routes_bp.route("/api/menu", methods=["GET"])
@login_required
@rol_required(['1', '2'])
def api_get_menu():
    productos = Producto.obtener_todo()
    return jsonify({"success": True, "menu": productos})

@routes_bp.route("/api/mesero/estadisticas/dia", methods=["GET"])
@login_required
@rol_required(['2'])
def api_mesero_estadisticas_dia():
    return ComandaController.estadisticas_dia_mesero()

@routes_bp.route("/api/mesero/mesas/estado", methods=["GET"])
@login_required
@rol_required(['2'])
def api_mesero_mesas_estado():
    return MesaController.estado_mesas_mesero()

@routes_bp.route("/api/mesero/mesa/<numero>", methods=["GET"])
@login_required
def api_mesero_mesa_detalle(numero):
    return MesaController.detalle_mesa(numero)

@routes_bp.route("/api/mesero/comandas/activas", methods=["GET"])
@login_required
@rol_required(['2'])
def api_mesero_comandas_activas():
    return ComandaController.comandas_activas()

@routes_bp.route("/api/mesero/cuenta/abrir", methods=["POST"])
@login_required
@rol_required(['2'])
def api_abrir_cuenta():
    return ComandaController.abrir_cuenta()

@routes_bp.route("/api/mesero/comanda/<cuenta_id>/items", methods=["POST"])
@login_required
@rol_required(['2'])
def api_guardar_items_comanda(cuenta_id):
    return ComandaController.guardar_items(cuenta_id)

@routes_bp.route("/api/mesero/cuenta/<cuenta_id>/cerrar", methods=["POST"])
@login_required
@rol_required(['2'])
def api_cerrar_cuenta(cuenta_id):
    return ComandaController.cerrar_cuenta(cuenta_id)

@routes_bp.route("/api/mesero/comandas/cerradas", methods=["GET"])
@login_required
@rol_required(['2'])
def api_comandas_cerradas():
    return ComandaController.comandas_cerradas()

@routes_bp.route("/api/mesero/propinas/hoy", methods=["GET"])
@login_required
@rol_required(['2'])
def api_propinas_hoy():
    return PropinasController.propinas_hoy()

@routes_bp.route("/api/mesero/propinas/rango", methods=["GET"])
@login_required
@rol_required(['2'])
def api_propinas_rango():
    return PropinasController.propinas_rango()

@routes_bp.route("/api/mesero/historial", methods=["GET"])
@login_required
@rol_required(['2'])
def api_mesero_historial():
    return HistorialController.historial_mesero()

@routes_bp.route("/api/mesero/kmeans", methods=["GET"])
@login_required
@rol_required(['2'])
def api_mesero_kmeans():
    return MeseroKMeansController.api_kmeans()

@routes_bp.route("/api/mesero/kmeans/recomendaciones", methods=["POST"])
@login_required
@rol_required(['2'])
def api_mesero_kmeans_recomendaciones():
    return MeseroKMeansController.api_recomendaciones()

@routes_bp.route("/api/mesero/kmeans/diagnostico", methods=["GET"])
@login_required
@rol_required(['2'])
def api_mesero_kmeans_diagnostico():
    return MeseroDiagnosticoController.api_diagnostico()

@routes_bp.route("/api/analytics/tendencias", methods=["GET"])
@login_required
@rol_required(['2'])
def api_tendencias():
    return jsonify(AnalyticsChartsService.tendencias())

@routes_bp.route("/api/analytics/histograma", methods=["GET"])
@login_required
@rol_required(['2'])
def api_histograma():
    return jsonify(AnalyticsChartsService.histograma())

@routes_bp.route("/api/analytics/heatmap", methods=["GET"])
@login_required
@rol_required(['2'])
def api_heatmap():
    return jsonify(AnalyticsChartsService.heatmap())

@routes_bp.route("/api/analytics/area", methods=["GET"])
@login_required
@rol_required(['2'])
def api_area():
    start_raw = request.args.get("start_date")
    end_raw = request.args.get("end_date")  # límite exclusivo (inicio de la semana siguiente)
    if start_raw and end_raw:
        try:
            fecha_inicio = datetime.strptime(start_raw, "%Y-%m-%d")
            fecha_fin_exclusiva = datetime.strptime(end_raw, "%Y-%m-%d")
        except ValueError:
            return jsonify({"success": False, "error": "Formato de fecha inválido, usa YYYY-MM-DD"}), 400
        if fecha_fin_exclusiva <= fecha_inicio:
            return jsonify({"success": False, "error": "end_date debe ser posterior a start_date"}), 400
        return jsonify(AnalyticsChartsService.area(fecha_inicio=fecha_inicio, fecha_fin_exclusiva=fecha_fin_exclusiva))
    return jsonify(AnalyticsChartsService.area())

@routes_bp.route("/api/analytics/boxplot", methods=["GET"])
@login_required
@rol_required(['2'])
def api_boxplot():
    return jsonify(AnalyticsChartsService.boxplot())
