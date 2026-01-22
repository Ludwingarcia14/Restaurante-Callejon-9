from flask import (
    Blueprint, request, session, jsonify, current_app, render_template,
    redirect, url_for, flash, abort
)
from bson.objectid import ObjectId
from datetime import datetime
import re
import os
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest

from services.ai_engine.orchestrator import procesar_perfil_background # <--- ¡Añadir!
import threading # <--- ¡Añadir!
from services.ai_engine.Ine_analyzer import analyze_ine_document # type: ignore # <--- ¡NUEVA IMPORTACIÓN!
from services.ai_engine.buro_credito_analyzer import BuroCreditoProcessor # type: ignore
from services.ai_engine.buro_analyser import BuroAnalyser # Ajusta la ruta de importación si es necesario
from services.scoring.scoring_service import FinancialScoringService
from utils.background_tasks_buro import procesar_buro_async

from utils.background_tasks_domicilio import procesar_domicilio_async # <-- ¡NUEVO!

# Modelos
from models.user_model import Usuario
from models.clienteModel import Cliente
from models.soporte_model import Ticket, FAQ
from models.documentofisica_model import DocumentoFisica
from models.documentomoral_model import DocumentoMoral

# ====================================================================
# 1. IMPORTACIONES CQRS
# ====================================================================

# Queries
from cqrs.queryes.client.get_dashboard_queries import GetDashboardQueries
from cqrs.queryes.client.get_profile_queries import GetProfileQueries
from cqrs.queryes.client.get_solicitud_queries import GetSolicitudQueries
from cqrs.queryes.client.get_asesor_queries import GetAsesorQueries
from cqrs.queryes.client.get_document_queries import GetDocumentQueries

# Commands
from cqrs.commands.client.change_password_command import ChangePasswordCommand
from cqrs.commands.client.create_solicitud_command import CreateSolicitudCommand
from cqrs.commands.client.upload_documents_command import UploadDocumentsCommand
from cqrs.commands.client.update_profile_command import UpdateProfileCommand
from cqrs.commands.client.edit_solicitud_command import EditSolicitudCommand
from cqrs.commands.client.delete_solicitud_command import DeleteSolicitudCommand
from cqrs.commands.client.create_ticket_command import CreateTicketCommand

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


class clientController:

    # ============================================================
    # DASHBOARD CLIENTE (QUERY)
    # ============================================================
    @staticmethod
    def DashboardClient():
        if "usuario_rol" in session and str(session["usuario_rol"]) == "4":

            cliente_id = session.get("usuario_id")
            tipo_persona = session.get("tipo_persona", "fisica").lower()
            
            # Inicializamos variables para la vista
            financial_score = None
            progreso = 0
            docs_subidos = 0
            docs_totales = 0
            doc_obj = None

            try:
                # ---------------------------------------------------------
                # 1. OBTENER EL DOCUMENTO (Expediente)
                # ---------------------------------------------------------
                if tipo_persona == 'fisica':
                    doc_obj = DocumentoFisica.get_by_user_id(cliente_id)
                    campo_estados = "estados_cuenta_fisica"
                    campos_req = [
                        'ine', 'domicilio', 'situacion_fiscal', 'buro_credito', 
                        'estados_cuenta', 'declaracion_anual', 'estados_financieros'
                    ]
                else:
                    doc_obj = DocumentoMoral.get_by_user_id(cliente_id)
                    campo_estados = "estados_cuenta_moral"
                    campos_req = [
                        'ine', 'domicilio', 'situacion_fiscal', 'buro_credito', 
                        'acta_constitutiva', 'poderes', 'declaracion_anual', 
                        'estados_financieros', 'estados_cuenta'
                    ]

                # ---------------------------------------------------------
                # 2. CALCULAR SCORE FINANCIERO (CORREGIDO)
                # ---------------------------------------------------------
                if doc_obj and doc_obj.raw_data:
                    # Extraemos la data cruda
                    docs_data = doc_obj.raw_data.get("documentos", {})
                    
                    # [PASO CLAVE] Buscar PRIMERO en el campo nuevo donde guarda la IA ahora
                    analisis_ia = docs_data.get("analisis_financiero")

                    # Si no lo encuentra ahí, busca en la ubicación antigua (Compatibilidad)
                    if not analisis_ia:
                        datos_estados = docs_data.get(campo_estados)
                        if isinstance(datos_estados, dict):
                            analisis_ia = datos_estados.get("analisis")
                        elif isinstance(datos_estados, list):
                            for item in datos_estados:
                                if isinstance(item, dict) and item.get("analisis"):
                                    analisis_ia = item.get("analisis")
                                    break
                    
                    # Si encontramos datos (en cualquiera de los dos lados), calculamos el Score
                    if analisis_ia:
                        # print("🤖 Calculando Score Financiero con datos de IA...")
                        financial_score = FinancialScoringService.calcular_score(analisis_ia)

                # ---------------------------------------------------------
                # 3. LÓGICA DE PROGRESO DEL EXPEDIENTE
                # ---------------------------------------------------------
                if doc_obj:
                    docs_totales = len(campos_req)
                    # Usamos getattr para verificar si el atributo del modelo tiene datos (ruta)
                    docs_subidos = sum(1 for c in campos_req if getattr(doc_obj, c, None))
                    
                    if docs_totales > 0:
                        progreso = int((docs_subidos / docs_totales) * 100)

                # ---------------------------------------------------------
                # 4. SOLICITUDES Y BURÓ
                # ---------------------------------------------------------
                solicitud_activa = GetDashboardQueries.get_active_solicitud(cliente_id, tipo_persona)
                analisis_mop = None

                if (solicitud_activa and 
                    solicitud_activa.get("documentos", {}).get(f"buro_credito_{tipo_persona}", {}).get("analisis_buro")):
                    
                    analisis_mop = BuroAnalyser.analizar_mop_buro(solicitud_activa)
                else:
                    analisis_mop = {
                        "resumen_mop_titulo": "Pendiente",
                        "estado_resumen": "secondary",
                        "resumen_mop_descripcion": "Aún no se ha procesado tu Buró de Crédito.",
                        "mop_alto_riesgo_detectado": False
                    }

                historial_creditos = GetDashboardQueries.get_historial_creditos(cliente_id)

                # ---------------------------------------------------------
                # 5. RENDERIZADO
                # ---------------------------------------------------------
                return render_template(
                    "client/dashboard.html",
                    usuario=session.get("usuario_nombre"),
                    solicitud_activa=solicitud_activa,
                    historial_creditos=historial_creditos,
                    analisis_mop=analisis_mop,
                    # Variables Calculadas
                    progreso=progreso,
                    docs_subidos=docs_subidos,
                    docs_totales=docs_totales,
                    financial_score=financial_score 
                )

            except Exception as e:
                current_app.logger.error(f"Error dashboard cliente: {e}", exc_info=True)
                return render_template("client/dashboard.html", error="Error cargando información", progreso=0)

        return redirect(url_for("routes.login"))


        # ============================================================
        # PERFIL CLIENTE (QUERY)
        # ============================================================
    @staticmethod
    def Perfil():
        usuario_id = session.get("usuario_id")
        cliente_data = GetProfileQueries.get_client_profile_data(usuario_id)
        return render_template("client/perfil.html", cliente=cliente_data)

        # ============================================================
        # CAMBIAR CONTRASEÑA (COMMAND)
        # ============================================================
    @staticmethod
    def CambiarPassword():
        if "usuario_id" not in session:
           return redirect(url_for("routes.login"))

        try:
            usuario_id = session.get("usuario_id")
            password_actual = request.form.get("usuario_clave")
            password_nueva = request.form.get("password_nueva")
            confirm_password = request.form.get("confirm_password")

            if password_nueva != confirm_password:
                flash("Las contraseñas nuevas no coinciden", "danger")
                return redirect(url_for("routes.dashboard_client"))

            ChangePasswordCommand(usuario_id, password_actual, password_nueva).execute()

            flash("Contraseña actualizada correctamente", "success")
            return redirect(url_for("routes.dashboard_client"))

        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("routes.dashboard_client"))

        except Exception as e:
            current_app.logger.error(f"Error al cambiar contraseña: {e}", exc_info=True)
            flash("Error al cambiar contraseña", "danger")
        return redirect(url_for("routes.dashboard_client"))

    # ============================================================
    # ACTUALIZAR PERFIL (COMMAND)
    # ============================================================
    @staticmethod
    def PerfilUpdate():
        if "usuario_rol" not in session:
            return redirect(url_for("routes.login"))

        try:
            usuario_id = session.get("usuario_id")
            UpdateProfileCommand(usuario_id, request.form.to_dict(), request.files).execute()

            flash("Perfil actualizado correctamente", "success")
            return redirect(url_for("routes.perfil_cliente"))

        except Exception as e:
            current_app.logger.error(f"Error al actualizar perfil del cliente: {e}", exc_info=True)
            flash("Error al actualizar perfil", "danger")
            return redirect(url_for("routes.perfil_cliente"))

    # ============================================================
    # LISTADO DE SOLICITUDES (QUERY)
    # ============================================================
    @staticmethod
    def CreditoView():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            usuario_id = ObjectId(session.get("usuario_id"))
            solicitudes = GetSolicitudQueries.get_solicitudes_with_asesor(usuario_id)

            return render_template("client/credito.html", solicitudes=solicitudes)

        except Exception as e:
            current_app.logger.error(f"Error al cargar CreditoView: {e}", exc_info=True)
            return render_template("client/credito.html", solicitudes=[], error="Error al cargar solicitudes.")

    # ============================================================
    # CREAR SOLICITUD (COMMAND)
    # ============================================================
    @staticmethod
    def CrearSolicitud():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        if request.method == "POST":
            try:
                usuario_id = ObjectId(session.get("usuario_id"))

                if not all(request.form.get(field) for field in ("monto", "plazo", "interes")):
                    flash("Todos los campos son obligatorios.", "warning")
                    return redirect(url_for("routes.credito_view"))

                CreateSolicitudCommand(usuario_id, request.form.to_dict()).execute()

                flash("Solicitud de crédito creada correctamente.", "success")
                return redirect(url_for("routes.credito_view"))

            except Exception as e:
                current_app.logger.error(f"Error al crear solicitud: {e}", exc_info=True)
                flash("Error al crear la solicitud. Inténtalo nuevamente.", "danger")
                return redirect(url_for("routes.credito_view"))

        return redirect(url_for("routes.credito_view"))

    # ============================================================
    # EDITAR SOLICITUD (COMMAND + QUERY)
    # ============================================================
    @staticmethod
    def EditarSolicitud(solicitud_id):
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        solicitud = GetSolicitudQueries.get_solicitud_by_id(solicitud_id)
        if not solicitud:
            abort(404, description="Solicitud no encontrada")

        if request.method == "POST":
            try:
                EditSolicitudCommand(solicitud_id, request.form.to_dict()).execute()
                flash("Solicitud actualizada correctamente.", "success")
                return redirect(url_for("routes.credito_view"))

            except Exception as e:
                current_app.logger.error(f"Error al editar solicitud: {e}", exc_info=True)
                flash("Error al actualizar la solicitud.", "danger")
                return redirect(url_for("routes.credito_view"))

        return render_template("client/editar_credito.html", solicitud=solicitud)

    # ============================================================
    # ELIMINAR SOLICITUD (COMMAND)
    # ============================================================
    @staticmethod
    def EliminarSolicitud(solicitud_id):
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            DeleteSolicitudCommand(solicitud_id).execute()
            flash("Solicitud eliminada correctamente.", "success")

        except Exception as e:
            current_app.logger.error(f"Error al eliminar solicitud: {e}", exc_info=True)
            flash("Error al eliminar la solicitud.", "danger")

        return redirect(url_for("routes.credito_view"))

    # ============================================================
    # DETALLE DE SOLICITUD (QUERY)
    # ============================================================
    @staticmethod
    def DetalleSolicitud(solicitud_id):
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        solicitud = GetSolicitudQueries.get_solicitud_by_id(solicitud_id)
        if not solicitud:
            abort(404, description="Solicitud no encontrada")

        asesor_id = solicitud.get("asesor")

        if asesor_id:
            asesor = GetSolicitudQueries.get_asesor_for_solicitud(asesor_id)
            solicitud["nombre_asesor"] = asesor.get("nombre", "-")
            solicitud["telefono_asesor"] = asesor.get("telefono", "-")
            solicitud["correo_asesor"] = asesor.get("correo", "-")
        else:
            solicitud.update({
                "nombre_asesor": "-",
                "telefono_asesor": "-",
                "correo_asesor": "-"
            })

        return render_template("client/detalle_credito.html", solicitud=solicitud)

    # ============================================================
    # HISTORIAL DE SOLICITUDES (QUERY)
    # ============================================================
    @staticmethod
    def HistorialSolicitudes():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            usuario_id = ObjectId(session.get("usuario_id"))
            solicitudes = GetSolicitudQueries.get_solicitudes_with_asesor(usuario_id)

            return render_template("client/historial.html", solicitudes=solicitudes)

        except Exception as e:
            current_app.logger.error(f"Error al cargar historial: {e}", exc_info=True)
            return render_template("client/historial.html", solicitudes=[], error="Error al cargar historial.")

    # ============================================================
    # ASESOR ASIGNADO (QUERY)
    # ============================================================
    @staticmethod
    def AsesorAsignado():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            cliente_id = session.get("usuario_id")
            reciente, citas = GetAsesorQueries.get_assigned_asesor_info_and_citas(cliente_id)

            if not reciente:
                return render_template(
                    "client/asesor_asignado.html",
                    error="No se encontró asesor asignado.",
                    reciente=None,
                    citas=[]
                )

            return render_template(
                "client/asesor_asignado.html",
                reciente=reciente,
                citas=citas
            )

        except Exception as e:
            current_app.logger.error(f"Error en AsesorAsignado: {e}", exc_info=True)
            return render_template(
                "client/asesor_asignado.html",
                error="Ocurrió un error al obtener la información del asesor.",
                reciente=None,
                citas=[]
            )

    # ============================================================
    # VISTA DOCUMENTOS (QUERY)
    # ============================================================
    @staticmethod
    def DocumentosView():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        try:
            usuario_id = ObjectId(session.get("usuario_id"))

            # 1. Obtener datos crudos de la BD (Diccionarios)
            data_fisica = GetDocumentQueries.get_documento_fisica(usuario_id)
            data_moral = GetDocumentQueries.get_documento_moral(usuario_id)

            # 2. Convertir a Objetos Inteligentes
            # Esto activa el __init__ que mapea las rutas para el HTML
            doc_fisica_obj = DocumentoFisica(data_fisica) if data_fisica else None
            doc_moral_obj = DocumentoMoral(data_moral) if data_moral else None

            # 3. Renderizar
            return render_template(
                "client/documentos.html",
                # Pasamos los OBJETOS, no los diccionarios crudos
                doc_fisica=doc_fisica_obj, 
                doc_moral=doc_moral_obj
            )

        except Exception as e:
            current_app.logger.error(f"Error en DocumentosView: {e}", exc_info=True)
            return redirect(url_for("routes.dashboard_client")) # Redirige al dashboard en caso de error

    # ============================================================
    # SUBIR DOCUMENTOS (COMMAND) - REVISADO
    # ============================================================
    @staticmethod
    def SubirDocumentos():
        try:
            if "usuario_id" not in session:
                return jsonify({"error": "No autorizado", "success": False}), 401

            usuario_id = session.get("usuario_id")
            app = current_app._get_current_object()

            # 1. Ejecutar Command
            # request.files se pasa directo. Flask maneja multipart automáticamente.
            resultado_comando = UploadDocumentsCommand(usuario_id, request.files).execute()

            mensaje_respuesta = "Documentos subidos correctamente."
            analisis_disparado = False

            # ===============================================================
            # 3. Analizar Estado de Cuenta (LISTA)
            # ===============================================================
            # Ahora esto es una lista: ['path1.pdf', 'path2.pdf']
            rutas_archivos = resultado_comando.get("archivo_para_analisis")

            if rutas_archivos and len(rutas_archivos) > 0:
                try:
                    hilo_cuenta = threading.Thread(
                        target=procesar_perfil_background,
                        # Pasamos la LISTA al orquestador
                        args=(app, usuario_id, rutas_archivos, "cuenta_bancaria")
                    )
                    hilo_cuenta.start()
                    current_app.logger.info(f"🧵 Hilo de análisis de Cuenta iniciado con {len(rutas_archivos)} archivos.")
                    mensaje_respuesta = f"Analizando {len(rutas_archivos)} estados de cuenta..."
                    analisis_disparado = True
                except Exception as thread_error:
                    current_app.logger.error(f"⚠️ Error hilo Cuenta: {thread_error}")

            # ===============================================================
            # 4. Analizar INE (MANTIENE INDIVIDUAL/DICT)
            # ===============================================================
            ine_archivos = resultado_comando.get("ine_archivos") # Es un Dict

            if ine_archivos:
                try:
                    hilo_ine = threading.Thread(
                        target=analyze_ine_document,
                        args=(app, usuario_id, ine_archivos)
                    )
                    hilo_ine.start()
                    current_app.logger.info(f"🧵 Hilo de análisis de INE iniciado para {usuario_id}")
                    if not analisis_disparado:
                        mensaje_respuesta = "Documentos recibidos. Analizando identidad..."
                    analisis_disparado = True
                except Exception as thread_error:
                    current_app.logger.error(f"⚠️ Error hilo INE: {thread_error}", exc_info=True)

            # ===============================================================
            # 5. Analizar Buró de Crédito (MANTIENE INDIVIDUAL/STRING)
            # ===============================================================
            buro_file_path = resultado_comando.get("buro_archivos") # Es un String

            if buro_file_path:
                try:
                    hilo_buro = threading.Thread(
                        target=procesar_buro_async,
                        args=(app, usuario_id, buro_file_path)
                    )
                    hilo_buro.start()
                    current_app.logger.info(f"🧵 Hilo de análisis de Buró iniciado para {usuario_id}")
                    if not analisis_disparado:
                        mensaje_respuesta = "Documentos recibidos. Analizando Buró..."
                    analisis_disparado = True
                except Exception as thread_error:
                    current_app.logger.error(f"⚠️ Error hilo Buró: {thread_error}", exc_info=True)

            # ===============================================================
            # 6. Analizar Domicilio (MANTIENE INDIVIDUAL/STRING)
            # ===============================================================
            domicilio_path = resultado_comando.get("domicilio_path") # Es un String

            if domicilio_path:
                try:
                    hilo_domicilio = threading.Thread(
                        target=procesar_domicilio_async,
                        args=(app, usuario_id, domicilio_path),
                        daemon=True
                    )
                    hilo_domicilio.start()
                    current_app.logger.info(f"🧵 Hilo de análisis de Domicilio iniciado para {usuario_id}")
                    if not analisis_disparado:
                        mensaje_respuesta = "Documentos recibidos. Analizando domicilio..."
                    analisis_disparado = True
                except Exception as thread_error:
                    current_app.logger.error(f"⚠️ Error hilo Domicilio: {thread_error}", exc_info=True)

            return jsonify({"success": True, "message": mensaje_respuesta}), 200

        except ValueError as ve:
            return jsonify({"error": str(ve), "success": False}), 400
        except Exception as e:
            current_app.logger.error(f"Error crítico subiendo documentos: {e}", exc_info=True)
            return jsonify({"error": "Error interno del servidor", "success": False}), 500


            # ===============================================================
            # 7. Respuesta final al cliente
            # ===============================================================
            return jsonify({"success": True, "message": mensaje_respuesta}), 200

        except ValueError as e:
            current_app.logger.warning(f"Error de validación al subir documentos: {e}")
            return jsonify({"error": str(e), "success": False}), 400

        except Exception as e:
            current_app.logger.error(f"Error en SubirDocumentos: {e}", exc_info=True)
            return jsonify({"error": "Error interno del servidor", "success": False}), 500


    # ============================================================
    # SOPORTE (QUERY)
    # ============================================================
    @staticmethod
    def VerSoporte():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        usuario_id = session.get("usuario_id")

        tickets = Ticket.obtener_tickets(usuario_id)
        faqs = FAQ.obtener_faq()
        whatsapp_soporte = "+5215551234567"

        return render_template(
            "client/soporte.html",
            tickets=tickets,
            faqs=faqs,
            whatsapp_soporte=whatsapp_soporte
        )

    # ============================================================
    # CREAR TICKET (COMMAND)
    # ============================================================
    @staticmethod
    def CrearTicket():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))

        if request.method == "POST":
            usuario_id = session.get("usuario_id")
            asunto = request.form.get("asunto")
            descripcion = request.form.get("descripcion")

            if not asunto or not descripcion:
                flash("Todos los campos son obligatorios.", "warning")
                return redirect(url_for("routes.soporte"))

            CreateTicketCommand(usuario_id, asunto, descripcion).execute()

            flash("Tu ticket se ha creado correctamente.", "success")
            return redirect(url_for("routes.soporte"))

        return redirect(url_for("routes.soporte"))

    def VerDocumentos():
        # Este método parece ser un remanente o ejemplo
        from flask import render_template, session
        
        usuario_id = session.get("usuario_id")
        # Aquí se debería poner la lógica si se utiliza una sola colección 'documentos'
        documentos = [] 
        return render_template("documentos.html", documentos=documentos)