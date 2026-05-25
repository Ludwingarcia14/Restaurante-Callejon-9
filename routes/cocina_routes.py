from flask import render_template, session, redirect, url_for
from controllers.auth.AuthController import login_required, rol_required
from controllers.dashboard.dashboard_controller import DashboardController
from controllers.cocina.cocinaController import CocinaController


def register_cocina_routes(bp):

    @bp.route("/dashboard/cocina")
    @login_required
    @rol_required(['3'])
    def dashboard_cocina():
        return DashboardController.cocina()

    @bp.route("/cocina/pedidos")
    @login_required
    @rol_required(['3'])
    def cocina_pedidos():
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "3":
            return redirect(url_for("routes.login"))
        perfil_cocina = session.get("perfil_cocina", {})
        return render_template("cocina/pedidos.html", perfil=perfil_cocina)

    @bp.route("/cocina/en-proceso")
    @login_required
    @rol_required(['3'])
    def cocina_en_proceso():
        return render_template("cocina/en_proceso.html")

    @bp.route("/cocina/listos")
    @login_required
    @rol_required(['3'])
    def cocina_listos():
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "3":
            return redirect(url_for("routes.login"))
        return render_template("cocina/listos.html")

    @bp.route("/api/cocina/pedidos/pendientes", methods=["GET"])
    @login_required
    @rol_required(['1', '3'])
    def api_cocina_pedidos_pendientes():
        return CocinaController.obtener_pedidos_pendientes()

    @bp.route("/api/cocina/pedidos/en-proceso", methods=["GET"])
    @login_required
    @rol_required(['1', '3'])
    def api_cocina_pedidos_en_proceso():
        return CocinaController.obtener_pedidos_en_proceso()

    @bp.route("/api/cocina/pedidos/listos", methods=["GET"])
    @login_required
    @rol_required(['1', '3'])
    def api_cocina_pedidos_listos():
        return CocinaController.obtener_pedidos_listos()

    @bp.route("/api/cocina/pedido/iniciar", methods=["POST"])
    @login_required
    @rol_required(['1', '3'])
    def api_cocina_iniciar_preparacion():
        return CocinaController.iniciar_preparacion()

    @bp.route("/api/cocina/pedido/listo", methods=["POST"])
    @login_required
    @rol_required(['1', '3'])
    def api_cocina_marcar_listo():
        return CocinaController.marcar_como_listo()

    @bp.route("/api/cocina/pedido/entregado", methods=["POST"])
    @login_required
    @rol_required(['1', '2', '3'])
    def api_cocina_marcar_entregado():
        return CocinaController.marcar_como_entregado()

    @bp.route("/api/cocina/estadisticas", methods=["GET"])
    @login_required
    @rol_required(['1', '3'])
    def api_cocina_estadisticas():
        return CocinaController.obtener_estadisticas_cocina()

    @bp.route("/api/cocina/charts/top-platillos", methods=["GET"])
    @login_required
    @rol_required(['1', '3'])
    def api_cocina_top_platillos():
        return CocinaController.get_top_platillos()

    @bp.route("/api/cocina/charts/kmeans", methods=["GET"])
    @login_required
    @rol_required(['1', '3'])
    def api_cocina_kmeans():
        return CocinaController.get_kmeans_platillos()
