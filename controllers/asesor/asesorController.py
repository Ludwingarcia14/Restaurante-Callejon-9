from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import qrcode
import io
import base64
import logging
import requests
from flask import (
    render_template,
    session,
    redirect,
    url_for,
    request,
    current_app,
)
from bson.objectid import ObjectId as BsonObjectId

from config.db import db

from services.scoring.scoring_service import FinancialScoringService

# Importar Query classes (Lectura)
from cqrs.queryes.asesor.get_asesor_queries import GetAsesorQueries
from cqrs.queryes.asesor.get_client_queries import GetClientQueries
from cqrs.queryes.asesor.get_solicitud_queries import GetSolicitudQueries
from cqrs.queryes.asesor.get_report_queries import GetReportQueries
# Importar Command classes (Escritura)
from cqrs.commands.asesor.create_task_command import CreateTaskCommand
from cqrs.commands.asesor.update_task_status_command import UpdateTaskStatusCommand
from cqrs.commands.asesor.delete_task_command import DeleteTaskCommand
from cqrs.commands.asesor.create_asesor_profile_command import CreateAsesorProfileCommand
from cqrs.commands.asesor.save_seguimiento_command import SaveSeguimientoCommand
from cqrs.commands.asesor.save_validacion_command import SaveValidacionCommand
from cqrs.commands.asesor.save_visita_command import SaveVisitaCommand
from cqrs.commands.asesor.approve_documents_command import ApproveDocumentsCommand


class asesorController:
    """Controlador para vistas y acciones relacionadas con asesores."""

    @staticmethod
    def _generate_qr_code_base64(data):
        """Genera un código QR y lo devuelve como imagen Base64 (PNG)."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Guardar la imagen en un buffer en memoria
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        
        # Codificar a Base64
        return base64.b64encode(buffer.getvalue()).decode()

    # -------------------------
    # DASHBOARD PRINCIPAL (QUERY) - CÓDIGO ACTUALIZADO 100% FUNCIONAL
    # -------------------------
    @staticmethod
    def DashboardAsesor():
        # 1. Verificación de Sesión
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ("1", "3"):
            return redirect(url_for("routes.login"))

        usuario_id_str = session.get("usuario_id")
        current_app.logger.debug(f"DashboardAsesor: Acceso ID {usuario_id_str}")

        # 2. Obtener Datos del Asesor
        asesor = GetAsesorQueries.get_user_by_id(usuario_id_str)
        
        # Intentar convertir a ObjectId para consultas que lo requieran
        try:
            usuario_obj_id = BsonObjectId(usuario_id_str) if usuario_id_str else None
        except Exception:
            usuario_obj_id = None

        if not asesor:
            return "Error: Asesor no encontrado. Verifique la sesión.", 500

        tipo_asesor = "interno" if asesor.get("usuario_tipo_asesor") == "interno" else "externo"

        # 3. Generación de QR y Link de Referencia
        asesor_referral_id = usuario_id_str
        BASE_REGISTRO_PATH = url_for("routes.register_client_saved", _external=True) # Apuntar a la ruta correcta
        # Aseguramos que la URL base esté limpia antes de agregar parámetros
        base_url_limpia = BASE_REGISTRO_PATH.split('?')[0]
        # Construimos el link final
        url_referencia = f"{base_url_limpia}?asesorID={asesor_referral_id}"
        qr_base64 = asesorController._generate_qr_code_base64(url_referencia)

        # 4. OBTENCIÓN DE DATOS REALES (QUERIES)
        # -------------------------------------------------
        
        # A. Clientes y Tareas
        lista_clientes = GetClientQueries.get_asesor_clients(usuario_obj_id) or []
        tareas = GetAsesorQueries.get_asesor_tasks(usuario_id_str) or []

        # B. Solicitudes y Cartera
        todas_solicitudes = GetSolicitudQueries.get_assigned_solicitudes(usuario_id_str) or []
        stats_credito = GetReportQueries.get_credit_stats(usuario_id_str)
        
        # Filtrar solicitudes activas (que no estén rechazadas ni liquidadas)
        solicitudes_activas = [
            s for s in todas_solicitudes 
            if s.get('estatus') not in ['RECHAZADO', 'LIQUIDADO', 'CANCELADO']
        ]
        
        # C. Procesar "Últimas Solicitudes" para la Tabla
        # Ordenamos por fecha (asumiendo campo 'created_at' o '_id' como proxy de tiempo)
        recientes_raw = sorted(todas_solicitudes, key=lambda x: x.get('_id', ''), reverse=True)[:5]
        solicitudes_recientes = []
        
        for sol in recientes_raw:
            # Buscar nombre del cliente para mostrar en la tabla
            cliente_info = GetClientQueries.get_client_by_id(sol.get('cliente_id'))
            nombre_cliente = "Cliente Desconocido"
            if cliente_info:
                nombre_cliente = f"{cliente_info.get('cliente_nombre', '')} {cliente_info.get('cliente_apellidos', '')}"
            
            # Formatear datos para la vista
            solicitudes_recientes.append({
                "_id": str(sol.get('_id')),
                "id_visible": str(sol.get('_id'))[-4:], # Últimos 4 dígitos
                "cliente_nombre": nombre_cliente,
                "estatus": sol.get('estatus', 'Pendiente'),
                "monto": float(sol.get('monto_solicitado', 0) or 0)
            })

        # D. Cálculo de Metas (Chart Data)
        # Definimos una meta mensual base (puedes hacerla dinámica luego guardándola en el perfil del asesor)
        META_MENSUAL = 500000.0 
        
        # Sumar montos de solicitudes APROBADAS este mes
        colocacion_actual = sum([
            float(s.get('monto_aprobado', 0) or 0) 
            for s in todas_solicitudes 
            if s.get('estatus') == 'APROBADO'
        ])
        
        # Calcular porcentaje
        porcentaje_meta = round((colocacion_actual / META_MENSUAL) * 100) if META_MENSUAL > 0 else 0
        porcentaje_meta = min(porcentaje_meta, 100) # Tope visual del 100%

        # Datos estructurados para pasar al JavaScript de la gráfica
        chart_data = {
            "meta_labels": ["Completado", "Restante"],
            "meta_values": [porcentaje_meta, 100 - porcentaje_meta],
            "colocacion_actual": colocacion_actual
        }

        # E. Métricas del Header (KPIs)
        metricas = {
            "clientes": len(lista_clientes),
            "solicitudes": len(solicitudes_activas),
            "visitas_hoy": 0, # Conectar con query de agenda si existe
            "cartera": stats_credito.get('total_creditos', 0),
            "cobranza_pendiente": stats_credito.get('morosos', 0),
            "creditos_activos": stats_credito.get('activos', 0)
        }

        # 5. Renderizar Vista
        return render_template(
            "asesor/dashboard.html",
            # Datos de Usuario
            usuario=asesor.get("usuario_nombre", "Asesor"),
            asesor=asesor,
            tipo_asesor=tipo_asesor,
            
            # Datos Operativos
            metricas=metricas,
            solicitudes_recientes=solicitudes_recientes,
            clientes=lista_clientes, # Para otras secciones si se usan
            tareas=tareas,
            
            # Datos para Gráficas y Metas
            chart_data=chart_data,
            colocacion_actual=colocacion_actual,
            meta_mensual=META_MENSUAL,
            
            # QR y Referencia
            url_referencia=url_referencia,
            qr_base64=qr_base64
        )

    # -------------------------
    # CREAR NUEVA TAREA (COMMAND)
    # -------------------------
    @staticmethod
    def tasks_create():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        data = request.get_json() if request.is_json else request.form.to_dict()
        asesor_id = session.get("usuario_id")

        try:
            CreateTaskCommand(asesor_id, data).execute()
            return redirect(url_for("routes.dashboard_asesor"))
        except Exception as e:
            current_app.logger.error("Error al crear tarea: %s", e, exc_info=True)
            return redirect(url_for("routes.dashboard_asesor"))

    # -------------------------
    # ACTUALIZAR STATUS DE TAREA (COMMAND)
    # -------------------------
    @staticmethod
    def task_update_status(tarea_id: str):
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            status = request.form.get("status")
            asesor_id = session["usuario_id"]

            if status not in ("pendiente", "en progreso", "completada"):
                return redirect(url_for("routes.dashboard_asesor"))

            UpdateTaskStatusCommand(tarea_id, asesor_id, status).execute()
            return redirect(url_for("routes.dashboard_asesor"))
        except Exception as e:
            current_app.logger.error("Error actualizando status tarea: %s", e, exc_info=True)
            return redirect(url_for("routes.dashboard_asesor"))

    # -------------------------
    # PERFIL DEL ASESOR (QUERY + COMMAND)
    # -------------------------
    @staticmethod
    def Perfil():
        if "usuario_id" not in session:
            current_app.logger.warning("Intento de acceso a perfil sin usuario_id en sesión")
            return redirect(url_for("routes.login"))

        try:
            usuario_id = session.get("usuario_id")
            current_app.logger.info("Buscando perfil para usuario_id: %s (tipo: %s)", usuario_id, type(usuario_id))

            usuario = GetAsesorQueries.get_user_by_id_or_usuario_id(usuario_id)
            asesor = GetAsesorQueries.get_asesor_by_usuario_id(usuario_id)

            if not asesor and usuario:
                current_app.logger.info("Creando registro de asesor automáticamente")
                asesor = CreateAsesorProfileCommand(usuario, usuario_id).execute()

            return render_template(
                "asesor/perfil.html",
                usuario=usuario,
                asesor=asesor,
                error=None if (usuario and asesor) else "Información incompleta del perfil",
            )
        except Exception as e:
            current_app.logger.error("Error crítico al cargar perfil del asesor: %s", e, exc_info=True)
            return render_template("asesor/perfil.html", usuario=None, asesor=None, error=f"Error: {e}")

    # -------------------------
    # SOLICITUDES ASIGNADAS (QUERY)
    # -------------------------
    @staticmethod
    def SolicitudesAsignadas():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            solicitudes = GetSolicitudQueries.get_assigned_solicitudes(session["usuario_id"])
            return render_template("asesor/solicitudes.html", solicitudes=solicitudes)
        except Exception as e:
            current_app.logger.error("Error al obtener solicitudes: %s", e, exc_info=True)
            return render_template("asesor/solicitudes.html", solicitudes=[], error=str(e))

    @staticmethod
    def listar_clientes_asesor():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            asesor_id = BsonObjectId(session["usuario_id"])
            lista_clientes = GetClientQueries.get_asesor_clients(asesor_id)
            return render_template("asesor/clientes/lista_clientes.html", clientes=lista_clientes)
        except Exception as e:
            logging.error("Error al listar clientes para asesor %s: %s", session.get("usuario_id"), e, exc_info=True)
            return redirect(url_for("routes.dashboard_asesor", error="No se pudieron cargar los clientes"))

    # -------------------------
    # SEGUIMIENTO DE CONTACTOS (QUERY / COMMAND)
    # -------------------------
    @staticmethod
    def Seguimiento(id_solicitud: str):
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            asesor_id = session["usuario_id"]
            solicitud = GetSolicitudQueries.get_solicitud_and_check_authorization(id_solicitud, asesor_id)

            if not solicitud:
                current_app.logger.warning("Solicitud no encontrada o no autorizada: %s", id_solicitud)
                return redirect(url_for("routes.dashboard_asesor"))

            contactos = GetSolicitudQueries.get_seguimiento_contactos(id_solicitud)
            return render_template("asesor/seguimiento.html", contactos=contactos, solicitud=solicitud, error=None)
        except Exception as e:
            current_app.logger.error("Error al obtener seguimiento: %s", e, exc_info=True)
            return render_template("asesor/seguimiento.html", contactos=[], solicitud=None, error=str(e))

    @staticmethod
    def SeguimientoGuardar(id_solicitud: str):
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            asesor_id = session["usuario_id"]
            solicitud = GetSolicitudQueries.get_solicitud_and_check_authorization(id_solicitud, asesor_id)

            if not solicitud:
                current_app.logger.warning("Solicitud no autorizada para guardar seguimiento: %s", id_solicitud)
                return redirect(url_for("routes.dashboard_asesor"))

            medio = request.form.get("medio", "").strip()
            comentarios = request.form.get("comentarios", "").strip()

            if not medio or not comentarios:
                current_app.logger.warning("Intento de guardar seguimiento con datos incompletos")
                return redirect(url_for("routes.asesor_seguimiento", id_solicitud=id_solicitud))

            data = request.form.to_dict()
            SaveSeguimientoCommand(id_solicitud, asesor_id, data).execute()
            current_app.logger.info("Seguimiento guardado exitosamente para solicitud: %s", id_solicitud)
            return redirect(url_for("routes.asesor_seguimiento", id_solicitud=id_solicitud))
        except Exception as e:
            current_app.logger.error("Error al guardar seguimiento: %s", e, exc_info=True)
            return redirect(url_for("routes.asesor_seguimiento", id_solicitud=id_solicitud))

    # -------------------------
    # CLIENTE - VISTA Y DOCUMENTOS (QUERY)
    # -------------------------
    @staticmethod
    def verCliente(id_cliente: str):
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            # 1. Obtener cliente y solicitudes
            cliente = GetClientQueries.get_client_by_id(id_cliente)
            if not cliente:
                return redirect(url_for("routes.asesor_clientes_lista", error="Cliente no encontrado"))

            cliente_obj_id = cliente["_id"]
            solicitudes = list(db["solicitudes"].find({"cliente_id": cliente_obj_id}).sort("fecha_creacion", -1))
            
            # 2. Obtener documentos
            documentos = GetClientQueries.get_client_all_documents(cliente_obj_id)
            docs_fisica = documentos.get("docs_fisica")
            docs_moral = documentos.get("docs_moral")
            
            # --- LÓGICA DE EXTRACCIÓN ROBUSTA (Igual al Dashboard Cliente) ---
            datos_sat = None
            analisis_financiero = None
            analisis_buro = None
            financial_score = None # Variable nueva

            # Determinar fuente de documentos y campo de estados de cuenta
            fuente_docs = docs_fisica if docs_fisica else docs_moral
            tipo_persona = "fisica" if docs_fisica else "moral"
            campo_estados = "estados_cuenta_fisica" if tipo_persona == "fisica" else "estados_cuenta_moral"

            if fuente_docs:
                # A) Datos SAT
                datos_sat = fuente_docs.get("datos_fiscales")
                
                # B) Análisis Financiero (Lógica de Fallback)
                # 1. Intentar buscar en la raíz (formato nuevo)
                analisis_financiero = fuente_docs.get("analisis_financiero")

                # 2. Si no existe, buscar dentro de la lista de estados de cuenta (formato antiguo)
                if not analisis_financiero:
                    datos_estados = fuente_docs.get(campo_estados)
                    if isinstance(datos_estados, list):
                        for item in datos_estados:
                            if isinstance(item, dict) and item.get("analisis"):
                                analisis_financiero = item.get("analisis")
                                break
                
                # C) Calcular Score Financiero (Si hay análisis)
                if analisis_financiero:
                    financial_score = FinancialScoringService.calcular_score(analisis_financiero)

                # D) Buró de Crédito
                clave_buro = f"buro_credito_{tipo_persona}"
                if clave_buro in fuente_docs and fuente_docs[clave_buro]:
                    analisis_buro = fuente_docs[clave_buro].get("analisis_buro")

            # 3. Renderizar
            return render_template(
                "asesor/clientes/view_cliente.html", 
                cliente=cliente, 
                solicitudes=solicitudes,
                tiene_documentos=bool(docs_fisica) or bool(docs_moral),
                datos_sat=datos_sat,
                analisis_financiero=analisis_financiero,
                analisis_buro=analisis_buro,
                financial_score=financial_score, # <--- Pasamos el score calculado
                error=None
            )

        except Exception as e:
            current_app.logger.error(f"Error verCliente: {e}", exc_info=True)
            print(f"❌ Error al cargar cliente {id_cliente}: {e}")
            return redirect(url_for("routes.asesor_clientes_lista", error="Error al cargar cliente"))

    @staticmethod
    def verClienteDocumentos(id_cliente: str):
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            cliente = GetClientQueries.get_client_by_id(id_cliente)
            if not cliente:
                return redirect(url_for("routes.asesor_clientes_lista", error="Cliente no encontrado"))

            cliente_obj_id = cliente["_id"]

            documentos = GetClientQueries.get_client_all_documents(cliente_obj_id) 
            print(documentos)
            return render_template(
                "asesor/clientes/view_documentos.html",
                cliente=cliente,
                docs_fisica=documentos["docs_fisica"],
                docs_moral=documentos["docs_moral"]
            )
        
        except Exception as e:
            current_app.logger.error("Error al buscar documentos del cliente: %s", e, exc_info=True)
            safe_id = str(id_cliente)
            return redirect(
                url_for("routes.dashboard_asesor_ver_cliente", id_cliente=safe_id, error="Error al cargar documentos")
            )

    # -------------------------
    # VALIDACIÓN DOCUMENTAL (QUERY / COMMAND)
    # -------------------------
    @staticmethod
    def Validacion(id_solicitud: str):
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            documentos = GetSolicitudQueries.get_documentos_solicitud(id_solicitud)
            return render_template("asesor/validacion.html", documentos=documentos, solicitud_id=id_solicitud)
        except Exception as e:
            current_app.logger.error("Error al obtener documentos: %s", e, exc_info=True)
            return render_template("asesor/validacion.html", documentos=[], solicitud_id=id_solicitud, error=str(e))

    @staticmethod
    def ValidacionActualizar(id_solicitud: str):
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            estado = request.form.get("estado")
            comentario = request.form.get("comentario")
            asesor_id = session["usuario_id"]

            SaveValidacionCommand(id_solicitud, asesor_id, estado, comentario).execute()
            return redirect(url_for("routes.asesor_validacion", id_solicitud=id_solicitud))
        except Exception as e:
            current_app.logger.error("Error al actualizar validación: %s", e, exc_info=True)
            return redirect(url_for("routes.asesor_validacion", id_solicitud=id_solicitud))

    # -------------------------
    # VISITA DOMICILIARIA (QUERY / COMMAND)
    # -------------------------
    @staticmethod
    def Visita(id_cliente: str):
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            visitas = GetClientQueries.get_visitas_cliente(id_cliente)
            cliente = GetAsesorQueries.get_user_by_id(id_cliente)
            return render_template("asesor/visita.html", cliente=cliente, visitas=visitas)
        except Exception as e:
            current_app.logger.error("Error al obtener visitas: %s", e, exc_info=True)
            return render_template("asesor/visita.html", cliente=None, visitas=[], error=str(e))

    @staticmethod
    def VisitaGuardar(id_cliente: str):
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            asesor_id = session["usuario_id"]
            data = request.form.to_dict()
            SaveVisitaCommand(id_cliente, asesor_id, data).execute()
            return redirect(url_for("routes.asesor_visita", id_cliente=id_cliente))
        except Exception as e:
            current_app.logger.error("Error al guardar visita: %s", e, exc_info=True)
            return redirect(url_for("routes.asesor_visita", id_cliente=id_cliente))

    # -------------------------
    # CARTERA POST-CRÉDITO (QUERY)
    # -------------------------
    @staticmethod
    def Cartera():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            creditos = GetSolicitudQueries.get_creditos_asesor(session["usuario_id"])
            return render_template("asesor/cartera.html", creditos=creditos)
        except Exception as e:
            current_app.logger.error("Error al obtener cartera: %s", e, exc_info=True)
            return render_template("asesor/cartera.html", creditos=[], error=str(e))

    # -------------------------
    # REPORTES DE DESEMPEÑO (QUERY)
    # -------------------------
    @staticmethod
    def Reportes():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            stats = GetReportQueries.get_credit_stats(session["usuario_id"])
            return render_template(
                "asesor/reportes.html",
                total_creditos=stats.get("total_creditos", 0),
                morosos=stats.get("morosos", 0),
                activos=stats.get("activos", 0),
            )
        except Exception as e:
            current_app.logger.error("Error al generar reportes: %s", e, exc_info=True)
            return render_template(
                "asesor/reportes.html", total_creditos=0, morosos=0, activos=0, error=str(e)
            )

    # -------------------------
    # NOTIFICACIONES (QUERY)
    # -------------------------
    @staticmethod
    def Notificaciones():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            notificaciones = GetAsesorQueries.get_asesor_notificaciones(session["usuario_id"])
            return render_template("asesor/notificaciones.html", notificaciones=notificaciones)
        except Exception as e:
            current_app.logger.error("Error al obtener notificaciones: %s", e, exc_info=True)
            return render_template("asesor/notificaciones.html", notificaciones=[], error=str(e))

    # -------------------------
    # DIAGNÓSTICO (DEBUG)
    # -------------------------
    @staticmethod
    def Diagnostico() -> Tuple[Dict[str, Any], int]:
        if "usuario_id" not in session:
            return {"error": "No hay sesión activa"}, 401

        try:
            usuario_id = session.get("usuario_id")
            diagnostico: Dict[str, Any] = {
                "session_info": {
                    "usuario_id": usuario_id,
                    "tipo": str(type(usuario_id)),
                    "usuario_nombre": session.get("usuario_nombre"),
                    "usuario_rol": session.get("usuario_rol"),
                },
                "colecciones": db.list_collection_names(),
                "usuario_existe": db["usuarios"].count_documents({"usuario_id": usuario_id}),
                "asesor_existe": db["asesores"].count_documents({"usuario_id": usuario_id}),
                "total_usuarios": db["usuarios"].count_documents({}),
                "total_asesores": db["asesores"].count_documents({}),
            }

            usuario_ejemplo = db["usuarios"].find_one({"usuario_id": usuario_id})
            if usuario_ejemplo:
                diagnostico["usuario_campos"] = list(usuario_ejemplo.keys())

            asesor_ejemplo = db["asesores"].find_one({"usuario_id": usuario_id})
            if asesor_ejemplo:
                diagnostico["asesor_campos"] = list(asesor_ejemplo.keys())

            return diagnostico, 200
        except Exception as e:
            return {"error": str(e)}, 500

    # -------------------------
    # ELIMINAR TAREA (COMMAND)
    # -------------------------
    @staticmethod
    def dashboard_task_delete(tarea_id: str):
        try:
            DeleteTaskCommand(tarea_id).execute()
        except Exception as e:
            current_app.logger.error("Error al eliminar tarea: %s", e, exc_info=True)
        return redirect(url_for("routes.dashboard_asesor"))

    # -------------------------
    # APROBAR / RECHAZAR DOCUMENTOS (COMMAND)
    # -------------------------
    @staticmethod
    def aprobar_documentos(id_cliente: str, es_aprobado: bool = True):
        if "usuario_id" not in session:
            return {"error": "No hay sesión activa"}, 401

        try:
            cliente = GetClientQueries.get_client_by_id(id_cliente)
            if not cliente:
                return redirect(url_for("routes.asesor_clientes_lista", error="Cliente no encontrado"))

            cliente_obj_id = cliente["_id"]
            mensajes_acciones = ApproveDocumentsCommand(id_cliente, es_aprobado).execute()
            estatus_final = "APROBADO" if es_aprobado else "RECHAZADO"

            # Notificación externa (intentar, pero no bloquear)
            url_node = "https://pyme-notificaciones.onrender.com/api/notificar"
            for accion in mensajes_acciones or []:
                if "APROBADO" in accion:
                    tipo_persona = accion.split(":")[0]
                    mensaje = f"Tus documentos de Persona {tipo_persona} han sido aprobados."
                    try:
                        requests.post(
                            url_node,
                            json={
                                "target": str(cliente_obj_id),
                                "evento": "DOCUMENTO_APROBADO",
                                "data": {"mensaje": mensaje, "hora": datetime.now().strftime("%Y-%m-%d %H:%M")},
                            },
                            timeout=3,
                        )
                    except Exception:
                        # Ignorar errores de notificación externa
                        current_app.logger.debug("Fallo al notificar a servicio externo (se ignora).")

            return {
                "mensaje": f"Proceso finalizado. Acciones: {', '.join(mensajes_acciones or [])}",
                "estatus_aplicado": estatus_final,
                "cliente": str(cliente_obj_id),
            }
        except Exception as e:
            current_app.logger.error("Error al aprobar/rechazar documentos: %s", e, exc_info=True)
            return {"error": f"Error interno: {e}"}, 500

    # -------------------------
    # LISTA DE VALIDACIONES (Método Nuevo)
    # -------------------------
    @staticmethod
    def ValidacionesLista():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            # Reutilizamos la query de solicitudes asignadas
            todas_solicitudes = GetSolicitudQueries.get_assigned_solicitudes(session["usuario_id"])
            
            # Opcional: Filtrar solo las que necesitan validación
            # validaciones_pendientes = [s for s in todas_solicitudes if s.get('estatus') in ['En revisión', 'Pendiente']]
            # Si prefieres mostrar todas y que el asesor elija, usa todas_solicitudes.
            
            return render_template("asesor/solicitudes.html", solicitudes=todas_solicitudes, titulo="Validación de Documentos")
        except Exception as e:
            current_app.logger.error("Error al obtener lista de validaciones: %s", e, exc_info=True)
            return render_template("asesor/solicitudes.html", solicitudes=[], error=str(e))