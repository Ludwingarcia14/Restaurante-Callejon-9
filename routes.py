"""
Módulo de Definición de Rutas (routes.py)

Este archivo centraliza la configuración de todas las URL (rutas) de la aplicación
utilizando un Flask Blueprint. Agrupa los endpoints y los enlaza a los métodos
correspondientes en los Controladores (Controllers) para cada módulo funcional:
Autenticación, Dashboard, Admin, Financiera, Asesor, Cliente e IA.
"""

from flask import Blueprint
# Importación de todos los controladores utilizados para enlazar las rutas
from controllers.auth.AuthController import AuthController
from controllers.dashboard.dashboard_controller import DashboardController
from controllers.admin.adminController import adminController
from controllers.api.apiController import apiController
from controllers.asesor.asesorController import asesorController
from controllers.support.supportController import supportController
from controllers.client.clientController import clientController
from controllers.financiera.financieraController import financieraController
from controllers.ia.ia_controller import iaController

# Creación del Blueprint de Rutas
routes_bp = Blueprint("routes", __name__)


# ------------------------------------------------------------
# 🔑 AUTENTICACIÓN Y ACCESO PÚBLICO
# ------------------------------------------------------------

# Home / Raíz: Llama al index que redirige a los Dashboards según el rol.
routes_bp.add_url_rule("/", view_func=DashboardController.index, endpoint="login2")

# Login de Usuarios (Administrativos/Asesores/Financieras)
routes_bp.add_url_rule("/login", view_func=AuthController.login, methods=["GET", "POST"], endpoint="login")

# Registro y Login de Clientes
routes_bp.add_url_rule("/register/client", view_func=DashboardController.registerClient, methods=["GET", "POST"], endpoint="registerClient")
routes_bp.add_url_rule("/register/client/saved", view_func=AuthController.register_client_saved, methods=["GET", "POST"], endpoint="register_client_saved")
routes_bp.add_url_rule("/login/client", view_func=DashboardController.loginClient, endpoint="login_client", methods=["GET", "POST"])

# Recuperación de Contraseña y Cierre de Sesión
routes_bp.add_url_rule("/retrieve/password", view_func=DashboardController.retrievepassword, endpoint="retrieve_password", methods=["GET", "POST"])
routes_bp.add_url_rule("/logout", view_func=AuthController.logout)


# ------------------------------------------------------------
# 💻 MÓDULO ADMINISTRADOR (ADMIN)
# ------------------------------------------------------------

# Vistas principales del Administrador
routes_bp.add_url_rule("/dashboard/admin", view_func=DashboardController.admin, endpoint="dashboard_Sadmin")
routes_bp.add_url_rule("/dashboard/admin/settings", view_func=adminController.settings, endpoint="dashboard_Sadmin_settings")
routes_bp.add_url_rule("/dashboard/admin/calendario", view_func=adminController.calendar, endpoint="dashboard_calendario")
routes_bp.add_url_rule("/dashboard/admin/stats", view_func=adminController.dashboard_stats, endpoint="dashboard_stats")

# Gestión de Usuarios Administrativos
routes_bp.add_url_rule('/dashboard/admin/lista', view_func=adminController.viewsAdmin, endpoint="dashboard_views_admin", methods=['GET'])
routes_bp.add_url_rule('/dashboard/admin/crear', view_func=adminController.create_admin, endpoint="dashboard_views_create_admin", methods=['GET'])
routes_bp.add_url_rule('/dashboard/admin/create', view_func=adminController.create_admin_post, endpoint="dashboard_create_admin", methods=['POST'])
routes_bp.add_url_rule('/dashboard/admin/data', view_func=adminController.get_usuarios_data, endpoint="get_usuarios_data", methods=['GET']) # API para dataTable

# CRUD de Usuarios (por ID)
routes_bp.add_url_rule("/admin/usuarios/delete/<usuario_id>", view_func=adminController.delete_usuario, methods=["POST"])
routes_bp.add_url_rule("/admin/usuarios/delete_batch", view_func=adminController.delete_usuarios_batch, methods=["POST"])
routes_bp.add_url_rule("/admin/usuarios/view/<usuario_id>", view_func=adminController.view_usuario)
routes_bp.add_url_rule("/admin/usuarios/edit/<usuario_id>", view_func=adminController.edit_usuario, methods=["POST"])

# Calendario
routes_bp.add_url_rule("/admin/calendario/eventos", view_func=adminController.eventos_calendar, endpoint="eventos_calendario_get",methods=["GET"])

# Gestión de Financieras (Instituciones)
routes_bp.add_url_rule('/dashboard/admin/financiera', view_func=adminController.createViewFinanciera, endpoint="dashboard_views_financiera", methods=['GET'])
routes_bp.add_url_rule('/dashboard/admin/financiera/lista', view_func=adminController.financieras_view_list, endpoint="dashboard_list_financiera", methods=['GET'])
routes_bp.add_url_rule('/admin/financiera/create', view_func=adminController.financieras_store, endpoint="financieras_store", methods=['POST'])
routes_bp.add_url_rule("/admin/financieras/data", view_func=adminController.financieras_data, methods=["GET"]) # API para dataTable
routes_bp.add_url_rule("/admin/financieras/view/<id>", view_func=adminController.financieras_view, endpoint="financieras_view",methods=["GET"])
routes_bp.add_url_rule("/admin/financieras/edit/<id>", view_func=adminController.financieras_edit, endpoint="financieras_edit",methods=["POST"])
routes_bp.add_url_rule("/admin/financieras/delete/<id>", view_func=adminController.financieras_delete, endpoint="financieras_delete",methods=["POST"])
routes_bp.add_url_rule("/admin/financieras/delete_batch", view_func=adminController.financieras_delete_batch, endpoint="financieras_delete_batch",methods=["POST"])

# Gestión de Clientes desde el Admin
routes_bp.add_url_rule("/dashboard/client/crear", view_func=adminController.crear_cliente, endpoint="dashboardA_client_create", methods=["GET"])
routes_bp.add_url_rule("/dashboard/client/create", view_func=adminController.dashboardA_client_list, endpoint="dashboardA_client_list", methods=["POST"])

# Configuración de Seguridad (2FA)
routes_bp.add_url_rule("/admin/config/generate/2fa", view_func=adminController.generate_2fa_setup, endpoint="generate_2fa_setup", methods=["POST"])
routes_bp.add_url_rule("/admin/config/verify/2fa", view_func=adminController.verify_and_enable_2fa, endpoint="verify_and_enable_2fa", methods=["POST"])
routes_bp.add_url_rule("/admin/config/disable/2fa", view_func=adminController.disable_2fa, endpoint="disable_2fa", methods=["POST"])


# ------------------------------------------------------------
# 🧠 MÓDULO INTELIGENCIA ARTIFICIAL (IA)
# ------------------------------------------------------------

# Vistas para la consulta de IA (desde el Admin)
routes_bp.add_url_rule('/dashboard/admin/ia/consulta/analizarsat', view_func=adminController.view_chat_ia, endpoint="view_chat_ia", methods=['GET'])
routes_bp.add_url_rule('/dashboard/admin/ia/consulta/estadoscuenta', view_func=adminController.view_estados_cuenta_ia, endpoint="view_estados_cuenta_ia", methods=['GET'])

# Endpoints de API para el análisis de IA
routes_bp.add_url_rule("/ia/analyze", view_func=iaController.analyze, endpoint="ia_analize", methods=["POST"])
routes_bp.add_url_rule("/ia/analyze/estados/cuenta", view_func=iaController.analyze_estados_cuenta, endpoint="analyze_estados_cuenta", methods=["POST"])


# ------------------------------------------------------------
# 🏦 MÓDULO FINANCIERA (Institución de Crédito)
# ------------------------------------------------------------

# Dashboard Principal y Data
routes_bp.add_url_rule("/dashboard/financiera", view_func=financieraController.Dashboardfinanciera, endpoint="dashboard_financiera")
routes_bp.add_url_rule("/dashboard/financiera/data", view_func=financieraController.get_asesores_data, endpoint="get_asesores_data", methods=['GET'])

# Gestión de Asesores de la Financiera
routes_bp.add_url_rule("/dashboard/financiera/asesor/create", view_func=financieraController.Dashboardasesor_create, endpoint="dashboard_asesorcreate")
routes_bp.add_url_rule("/dashboard/financiera/editar/asesor", view_func=financieraController.Dashboardasesor_edit, endpoint="dashboard_asesor_editar", methods=['GET'])
routes_bp.add_url_rule("/dashboard/financiera/lista/asesor", view_func=financieraController.Dashboardasesor_lista, endpoint="dashboard_asesor_lista", methods=['GET'])
routes_bp.add_url_rule("/financiera/asesor/create", view_func=financieraController.create_asesor_post, endpoint="create_asesor_post", methods=["POST"])

# --- Vistas de Proyección (KPIs y Reportes) ---
routes_bp.add_url_rule("/dashboard/financiera/proyeccion/liquidados", view_func=financieraController.proyeccion_liquidados, endpoint="dashboard_liquidados")
routes_bp.add_url_rule("/dashboard/financiera/proyeccion/mora", view_func=financieraController.proyeccion_mora, endpoint="dashboard_mora")
routes_bp.add_url_rule("/dashboard/financiera/proyeccion/pagos", view_func=financieraController.proyeccion_pagos, endpoint="dashboard_pagos")
routes_bp.add_url_rule("/dashboard/financiera/proyeccion/prestamos", view_func=financieraController.proyeccion_prestamos, endpoint="dashboard_prestamos")

# --- APIs de Proyección (Datos para Gráficas/Tablas) ---
routes_bp.add_url_rule("/api/reporte/liquidaciones", view_func=financieraController.api_reporte_liquidaciones, endpoint="api_reporte_liquidaciones", methods=['GET'])
routes_bp.add_url_rule("/api/reporte/mora", view_func=financieraController.api_reporte_mora, endpoint="api_reporte_mora", methods=['GET'])
routes_bp.add_url_rule("/api/reporte/pagos", view_func=financieraController.api_reporte_pagos, endpoint="api_reporte_pagos", methods=['GET'])
routes_bp.add_url_rule("/api/reporte/prestamos", view_func=financieraController.api_reporte_prestamos, endpoint="api_reporte_prestamos", methods=['GET'])

# --- Gestión de Préstamos ---
routes_bp.add_url_rule("/dashboard/financiera/gestion/prestamos", view_func=financieraController.Dashboardgestionprestamos, endpoint="dashboard_gestion_prestamos")
routes_bp.add_url_rule("/dashboard/financiera/gestion/prestamos/update", view_func=financieraController.Dashboardgestion_prestamos_update, endpoint="dashboardgestion_prestamos_update", methods=['POST'])

# Vistas de listado, detalle, edición y creación de Préstamos
routes_bp.add_url_rule("/dashboard/financiera/prestamos/lista", view_func=financieraController.view_prestamos_lista, endpoint="prestamos_lista", methods=["GET"])
routes_bp.add_url_rule("/dashboard/financiera/prestamos/data", view_func=financieraController.get_prestamos_data, endpoint="get_prestamos_data", methods=["GET"]) # API
routes_bp.add_url_rule("/dashboard/financiera/prestamos/ver/<id_prestamo>", view_func=financieraController.view_prestamo_detalle, endpoint="prestamo_detalle", methods=["GET"])
routes_bp.add_url_rule("/dashboard/financiera/prestamos/editar/<id_prestamo>", view_func=financieraController.view_prestamo_editar, endpoint="prestamo_editar", methods=["GET"])
routes_bp.add_url_rule("/dashboard/financiera/prestamos/update", view_func=financieraController.update_prestamo, endpoint="prestamo_update", methods=["POST"])
routes_bp.add_url_rule("/dashboard/financiera/prestamos/crear", view_func=financieraController.view_prestamo_crear, endpoint="prestamo_crear", methods=["GET"])
routes_bp.add_url_rule("/dashboard/financiera/prestamos/store", view_func=financieraController.store_prestamo, endpoint="prestamo_store", methods=["POST"])

# --- Gestión de Evaluaciones ---
routes_bp.add_url_rule("/dashboard/financiera/evaluacion/crear", view_func=financieraController.create_evaluacion, endpoint="dashboard_create_evaluacion", methods=["GET"])
routes_bp.add_url_rule("/dashboard/financiera/evaluaciones/lista", view_func=financieraController.views_evaluaciones, endpoint="dashboard_views_evaluaciones", methods=["GET"])
routes_bp.add_url_rule("/dashboard/financiera/evaluacion/create", view_func=financieraController.create_evaluacion_post, endpoint="create_evaluacion_post", methods=["POST"])
routes_bp.add_url_rule("/dashboard/financiera/evaluaciones/data", view_func=financieraController.get_evaluaciones_data, endpoint="get_evaluaciones_data", methods=["GET"])

# --- Configuración del Módulo Financiera ---
routes_bp.add_url_rule("/dashboard/financiera/configuracion", view_func=financieraController.dashboard_configuracion, endpoint="dashboard_configuracion", methods=["GET"])
routes_bp.add_url_rule("/dashboard/financiera/configuracion/general", view_func=financieraController.configuracion_general, endpoint="configuracion_general", methods=["GET"])
routes_bp.add_url_rule("/financiera/configuracion/general/update", view_func=financieraController.update_configuracion_general, endpoint="update_configuracion_general", methods=["POST"])

# Gestión de Catálogos (Tablas de referencia)
routes_bp.add_url_rule("/dashboard/financiera/configuracion/catalogos", view_func=financieraController.catalogos, endpoint="catalogos", methods=["GET"])
routes_bp.add_url_rule("/financiera/catalogos/data", view_func=financieraController.get_catalogos_data, endpoint="get_catalogos_data", methods=["GET"])
routes_bp.add_url_rule("/financiera/catalogos/create", view_func=financieraController.create_catalogo, endpoint="create_catalogo", methods=["POST"])
routes_bp.add_url_rule("/financiera/catalogos/view/<catalogo_id>", view_func=financieraController.view_catalogo, endpoint="view_catalogo", methods=["GET"])
routes_bp.add_url_rule("/financiera/catalogos/edit/<catalogo_id>", view_func=financieraController.edit_catalogo, endpoint="edit_catalogo", methods=["POST"])
routes_bp.add_url_rule("/financiera/catalogos/delete/<catalogo_id>", view_func=financieraController.delete_catalogo, endpoint="delete_catalogo", methods=["POST"])

# Auditoría
routes_bp.add_url_rule("/dashboard/financiera/configuracion/auditoria", view_func=financieraController.auditoria, endpoint="auditoria", methods=["GET"])
routes_bp.add_url_rule("/financiera/auditoria/data", view_func=financieraController.get_auditoria_data, endpoint="get_auditoria_data", methods=["GET"])
routes_bp.add_url_rule("/financiera/auditoria/view/<auditoria_id>", view_func=financieraController.view_auditoria, endpoint="view_auditoria", methods=["GET"])

# --- Vistas de Consultas y Reportes ---
routes_bp.add_url_rule("/dashboard/financiera/consultas/reportes", view_func=financieraController.obtener_conteo_clientes, endpoint="dashboard_consulta_reporte")
routes_bp.add_url_rule("/dashboard/financiera/clientes/count", view_func=financieraController.api_conteo_clientes, endpoint="api_conteo_clientes")

# Notificaciones
routes_bp.add_url_rule("/api/notificar/<id_usuario>", view_func=financieraController.api_reporte_prestamos, endpoint="api_reporte_prestamos", methods=['GET']) # Se usa el mismo endpoint, revisar si es un error de copia.


# ------------------------------------------------------------
# 🧑‍💼 MÓDULO ASESOR DE CRÉDITO
# ------------------------------------------------------------

# Dashboard y Funcionalidades Generales
routes_bp.add_url_rule("/dashboard/asesor", view_func=asesorController.DashboardAsesor, endpoint="dashboard_asesor")
routes_bp.add_url_rule('/toggle/theme', view_func=DashboardController.toggle_theme, endpoint='toggle_theme')

# Gestión de Tareas
routes_bp.add_url_rule("/dashboard/asesor/task/create", view_func=asesorController.tasks_create, methods=["POST"], endpoint="asesor_task_create")
routes_bp.add_url_rule('/dashboard/asesor/task/<tarea_id>/status', view_func=asesorController.task_update_status, methods=['POST'], endpoint='dashboard_task_update_status')
routes_bp.add_url_rule("/dashboard/asesor/task/delete/<tarea_id>", view_func=asesorController.dashboard_task_delete, methods=["POST"], endpoint="dashboard_task_delete")

# Clientes Asignados y Perfil
routes_bp.add_url_rule('/dashboard/asesor/clientes/lista', view_func=asesorController.listar_clientes_asesor, endpoint='asesor_clientes_lista', methods=['GET'])
routes_bp.add_url_rule("/dashboard/asesor/cliente/view/<id_cliente>", view_func=asesorController.verCliente, endpoint="dashboard_asesor_ver_cliente")
routes_bp.add_url_rule("/asesor/perfil", view_func=asesorController.Perfil, endpoint="asesor_perfil")

# Solicitudes y Documentación
routes_bp.add_url_rule("/asesor/solicitudes", view_func=asesorController.SolicitudesAsignadas, endpoint="asesor_solicitudes")
routes_bp.add_url_rule("/asesor/cliente/<id_cliente>/documentos", view_func=asesorController.verClienteDocumentos, endpoint="asesor_cliente_documentos", methods=['GET'])
routes_bp.add_url_rule("/asesor/cliente/<id_cliente>/aprobar", view_func=asesorController.aprobar_documentos, endpoint="asesor_cliente_aprobar_documentos", methods=['POST'])

# Seguimiento
routes_bp.add_url_rule("/asesor/seguimiento/<id_solicitud>", view_func=asesorController.Seguimiento, endpoint="asesor_seguimiento")
routes_bp.add_url_rule("/asesor/seguimiento/<id_solicitud>/guardar", view_func=asesorController.SeguimientoGuardar, methods=["POST"], endpoint="asesor_seguimiento_guardar")

# Validación Documental
routes_bp.add_url_rule("/asesor/validacion/<id_solicitud>", view_func=asesorController.Validacion, endpoint="asesor_validacion")
routes_bp.add_url_rule("/asesor/validacion/<id_solicitud>/actualizar", view_func=asesorController.ValidacionActualizar, methods=["POST"], endpoint="asesor_validacion_actualizar")

# Visitas Domiciliarias
routes_bp.add_url_rule("/asesor/visita/<id_cliente>", view_func=asesorController.Visita, endpoint="asesor_visita")
routes_bp.add_url_rule("/asesor/visita/<id_cliente>/guardar", view_func=asesorController.VisitaGuardar, methods=["POST"], endpoint="asesor_visita_guardar")

# Cartera, Reportes y Notificaciones
routes_bp.add_url_rule("/asesor/cartera", view_func=asesorController.Cartera, endpoint="asesor_cartera")
routes_bp.add_url_rule("/asesor/reportes", view_func=asesorController.Reportes, endpoint="asesor_reportes")
routes_bp.add_url_rule("/asesor/notificaciones", view_func=asesorController.Notificaciones, endpoint="asesor_notificaciones")

# Rutas de Diagnóstico (Definidas con @routes_bp.route)
@routes_bp.route("/asesor/diagnostico-solicitudes")
def diagnostico_solicitudes():
    """Diagnóstico de la etapa actual de las solicitudes."""
    return asesorController.DiagnosticoSolicitudes()
@routes_bp.route("/asesor/corregir-datos")
def corregir_datos_asesor():
    """Vista para la corrección manual de datos del asesor."""
    return asesorController.CorregirDatosAsesor()


# ------------------------------------------------------------
# 👤 MÓDULO CLIENTE
# ------------------------------------------------------------

# Perfil y Seguridad
routes_bp.add_url_rule("/dashboard/client", view_func=DashboardController.DashboardClient, endpoint="dashboard_client")
routes_bp.add_url_rule("/dashboard/client/perfil", view_func=clientController.Perfil, endpoint="perfil_cliente", methods=["GET"])
routes_bp.add_url_rule("/cliente/perfil", view_func=clientController.Perfil, endpoint="perfil_cliente", methods=["GET"])
routes_bp.add_url_rule("/cliente/perfil/update", view_func=clientController.PerfilUpdate, endpoint="PerfilUpdate", methods=["POST"])
routes_bp.add_url_rule("/cliente/perfil/password", view_func=clientController.CambiarPassword, endpoint="CambiarPassword", methods=["POST"])

# Documentación
routes_bp.add_url_rule("/dashboard/client/documentos", view_func=clientController.DocumentosView, endpoint="documentos_view")
routes_bp.add_url_rule("/dashboard/client/documentos/subir", view_func=clientController.SubirDocumentos, methods=["POST"], endpoint="subir_documentos")
routes_bp.add_url_rule("/dashboard/client/documentos/ver", view_func=clientController.VerDocumentos, endpoint="ver_documentos")

# Solicitudes de Crédito
routes_bp.add_url_rule("/dashboard/client/credito", view_func=clientController.CreditoView, endpoint="credito_view") # Ver todas las solicitudes
routes_bp.add_url_rule("/dashboard/client/credito/crear", view_func=clientController.CrearSolicitud, endpoint="crear_credito", methods=["POST"])
routes_bp.add_url_rule("/dashboard/client/credito/editar/<solicitud_id>", view_func=clientController.EditarSolicitud, endpoint="editar_credito", methods=["GET", "POST"])
routes_bp.add_url_rule("/dashboard/client/credito/eliminar/<solicitud_id>", view_func=clientController.EliminarSolicitud, endpoint="eliminar_credito")
routes_bp.add_url_rule("/dashboard/client/credito/detalle/<solicitud_id>", view_func=clientController.DetalleSolicitud, endpoint="detalle_credito")
routes_bp.add_url_rule("/dashboard/client/credito/historial", view_func=clientController.HistorialSolicitudes, endpoint="historial_credito")

# Soporte
routes_bp.add_url_rule("/dashboard/client/soporte", view_func=clientController.VerSoporte, endpoint="soporte")
routes_bp.add_url_rule("/dashboard/client/soporte/crear", view_func=clientController.CrearTicket, endpoint="crear_ticket", methods=["POST"])

# Información del Asesor Asignado
routes_bp.add_url_rule("/dashboard/client/asesor", view_func=clientController.AsesorAsignado, endpoint="asesor_asignado")


# ------------------------------------------------------------
# ===========================================
# 🛠️ MÓDULO SOPORTE TÉCNICO
# ===========================================

# Dashboard principal
routes_bp.add_url_rule("/dashboard/soporte",view_func=supportController.Dashboardsoporte,endpoint="dashboard_soporte")
# Comunicación / Chat
routes_bp.add_url_rule("/dashboard/soporte/comunicacion",view_func=supportController.ChatFAQ,methods=["GET"],endpoint="soporte_comunicacion")
# Alertas
routes_bp.add_url_rule("/dashboard/soporte/alertas",view_func=supportController.AlertasSoporte,endpoint="soporte_alertas")
# Historial
routes_bp.add_url_rule("/dashboard/soporte/historial",view_func=supportController.HistorialSoporte,endpoint="soporte_historial")
# Métricas
routes_bp.add_url_rule("/dashboard/soporte/metricas",view_func=supportController.MetricasSoporte,endpoint="soporte_metricas")
# Gestión de equipo
routes_bp.add_url_rule("/dashboard/soporte/gestion",view_func=supportController.GestionEquipo,endpoint="soporte_gestion")
# Tickets activos
routes_bp.add_url_rule("/dashboard/soporte/tickets",view_func=supportController.TicketsActivos,endpoint="soporte_tickets")
# Dashboard data
routes_bp.add_url_rule("/api/dashboard/soporte",view_func=supportController.DashboardData,endpoint="api_dashboard_soporte")
# Actualizar ticket
routes_bp.add_url_rule("/api/soporte/actualizar-ticket",view_func=supportController.ActualizarTicket,methods=["POST"],endpoint="api_actualizar_ticket")
# FAQ – procesar pregunta
routes_bp.add_url_rule("/api/soporte/procesar-pregunta",view_func=supportController.ProcesarPreguntaFAQ,methods=["POST"],endpoint="procesar_pregunta_faq")


# ------------------------------------------------------------
# 🌐 APIs EXTERNAS (Sepomex, Divisas, Bolsa)
# ------------------------------------------------------------
routes_bp.add_url_rule("/api/sepomex/estados", view_func=apiController.extract_estados)
routes_bp.add_url_rule("/api/sepomex/municipios/<estado_id>", view_func=apiController.extract_municipios)
routes_bp.add_url_rule("/api/sepomex/colonias/<municipio_id>", view_func=apiController.extract_colonias)
routes_bp.add_url_rule("/api/sepomex/cp/<cp>", view_func=apiController.extract_cp)
routes_bp.add_url_rule("/api/divisas/", view_func=apiController.get_divisas_data, endpoint="divisas_data")
routes_bp.add_url_rule("/api/bolsa/", view_func=apiController.get_bolsa_data, endpoint="bolsa_data")
routes_bp.add_url_rule("/api/me/", view_func=apiController.get_my_data, endpoint="api_me")