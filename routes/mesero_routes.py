from flask import render_template, session, redirect, url_for, jsonify
from controllers.auth.AuthController import login_required, rol_required
from controllers.dashboard.dashboard_controller import DashboardController
from controllers.comanda.comandaController import ComandaController
from controllers.mesa.mesaController import MesaController
from controllers.propina.propinasController import PropinasController
from controllers.historial.historialController import HistorialController
from controllers.mesero.kmeans_controller import MeseroKMeansController
from controllers.mesero.randomforest_controller import MeseroRandomForestController
from controllers.mesero.diagnostico_controller import MeseroDiagnosticoController
from controllers.mesero.metodologia_controller import MeseroMetodologiaController
from models.producto_model import Producto


def register_mesero_routes(bp):

    @bp.route("/dashboard/mesero")
    @login_required
    @rol_required(['2'])
    def dashboard_mesero():
        return DashboardController.mesero()

    @bp.route("/mesero/mesas")
    @login_required
    @rol_required(['2'])
    def mesero_mesas():
        return redirect(url_for("routes.dashboard_mesero"))

    @bp.route("/mesero/comandas")
    @login_required
    @rol_required(['2'])
    def mesero_comandas():
        perfil_mesero = session.get("perfil_mesero")
        if not perfil_mesero:
            return redirect(url_for("routes.login"))
        return render_template(
            "mesero/comandas.html",
            perfil=perfil_mesero,
            stats={"mesas_asignadas": perfil_mesero.get("mesas_asignadas", [])}
        )

    @bp.route("/mesero/menu")
    @login_required
    @rol_required(['2'])
    def mesero_menu():
        perfil_mesero = session.get("perfil_mesero")
        if not perfil_mesero:
            return redirect(url_for("routes.login"))
        return render_template(
            "mesero/mesero_menu.html",
            perfil=perfil_mesero,
            stats={"mesas_asignadas": perfil_mesero.get("mesas_asignadas", [])}
        )

    @bp.route("/mesero/propinas")
    @login_required
    @rol_required(['2'])
    def mesero_propinas():
        perfil_mesero = session.get("perfil_mesero")
        if not perfil_mesero:
            return redirect(url_for("routes.login"))
        return render_template("mesero/mesero_propinas.html", perfil=perfil_mesero)

    @bp.route("/mesero/historial")
    @login_required
    @rol_required(['2'])
    def mesero_historial():
        perfil_mesero = session.get("perfil_mesero")
        if not perfil_mesero:
            return redirect(url_for("routes.login"))
        return render_template("mesero/mesero_historial.html", perfil=perfil_mesero)

    @bp.route("/mesero/kmeans")
    @login_required
    @rol_required(['2'])
    def mesero_kmeans():
        return MeseroKMeansController.vista()

    @bp.route("/mesero/arbol")
    @login_required
    @rol_required(['2'])
    def mesero_arbol():
        return MeseroRandomForestController.vista()

    @bp.route("/mesero/diagnostico")
    @login_required
    @rol_required(['2'])
    def mesero_diagnostico():
        return MeseroDiagnosticoController.vista()

    @bp.route("/mesero/metodologia")
    @login_required
    @rol_required(['2'])
    def mesero_metodologia():
        return MeseroMetodologiaController.vista()

    # Ruta general de menú — registrada después que la de admin, preservando el comportamiento original
    @bp.route("/api/menu", methods=["GET"])
    @login_required
    @rol_required(['1', '2'])
    def api_get_menu():
        productos = Producto.obtener_todo()
        return jsonify({"success": True, "menu": productos})

    @bp.route("/api/mesero/estadisticas/dia", methods=["GET"])
    @login_required
    @rol_required(['2'])
    def api_mesero_estadisticas_dia():
        return ComandaController.estadisticas_dia_mesero()

    @bp.route("/api/mesero/mesas/estado", methods=["GET"])
    @login_required
    @rol_required(['2'])
    def api_mesero_mesas_estado():
        return MesaController.estado_mesas_mesero()

    @bp.route("/api/mesero/mesa/<numero>", methods=["GET"])
    @login_required
    def api_mesero_mesa_detalle(numero):
        return MesaController.detalle_mesa(numero)

    @bp.route("/api/mesero/comandas/activas", methods=["GET"])
    @login_required
    @rol_required(['2'])
    def api_mesero_comandas_activas():
        return ComandaController.comandas_activas()

    @bp.route("/api/mesero/cuenta/abrir", methods=["POST"])
    @login_required
    @rol_required(['2'])
    def api_abrir_cuenta():
        return ComandaController.abrir_cuenta()

    @bp.route("/api/mesero/comanda/<cuenta_id>/items", methods=["POST"])
    @login_required
    @rol_required(['2'])
    def api_guardar_items_comanda(cuenta_id):
        return ComandaController.guardar_items(cuenta_id)

    @bp.route("/api/mesero/cuenta/<cuenta_id>/cerrar", methods=["POST"])
    @login_required
    @rol_required(['2'])
    def api_cerrar_cuenta(cuenta_id):
        return ComandaController.cerrar_cuenta(cuenta_id)

    @bp.route("/api/mesero/comandas/cerradas", methods=["GET"])
    @login_required
    @rol_required(['2'])
    def api_comandas_cerradas():
        return ComandaController.comandas_cerradas()

    @bp.route("/api/mesero/propinas/hoy", methods=["GET"])
    @login_required
    @rol_required(['2'])
    def api_propinas_hoy():
        return PropinasController.propinas_hoy()

    @bp.route("/api/mesero/propinas/rango", methods=["GET"])
    @login_required
    @rol_required(['2'])
    def api_propinas_rango():
        return PropinasController.propinas_rango()

    @bp.route("/api/mesero/historial", methods=["GET"])
    @login_required
    @rol_required(['2'])
    def api_mesero_historial():
        return HistorialController.historial_mesero()

    @bp.route("/api/mesero/kmeans", methods=["GET"])
    @login_required
    @rol_required(['2'])
    def api_mesero_kmeans():
        return MeseroKMeansController.api_kmeans()

    @bp.route("/api/mesero/kmeans/diagnostico", methods=["GET"])
    @login_required
    @rol_required(['2'])
    def api_mesero_kmeans_diagnostico():
        return MeseroDiagnosticoController.api_diagnostico()
