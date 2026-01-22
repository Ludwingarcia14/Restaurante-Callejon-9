from flask import Blueprint, request, session, jsonify, current_app, render_template, redirect, url_for, flash, abort
from bson.objectid import ObjectId
from config.db import db
from datetime import datetime
import subprocess
import uuid
import bcrypt
import re
import logging
from werkzeug.exceptions import BadRequest
from models.financiera import Financiera
from pymongo.errors import PyMongoError
from collections import defaultdict
import pandas as pd
import numpy as np
import json

# ====================================================================
# 1. IMPORTACIONES DE CQRS
# ====================================================================
# Queries
from cqrs.queryes.financiera.get_dashboard_queries import GetDashboardQueries
from cqrs.queryes.financiera.get_asesor_queries import GetAsesorQueries
from cqrs.queryes.financiera.get_config_queries import GetConfigQueries
from cqrs.queryes.financiera.get_catalogo_queries import GetCatalogoQueries 
from cqrs.queryes.financiera.get_evaluacion_queries import GetEvaluacionQueries
from cqrs.queryes.prestamos.get_prestamo_detail_queries import GetPrestamoDetailQueries
from cqrs.queryes.prestamos.get_proyeccion_queries import GetProyeccionQueries 
from cqrs.queryes.prestamos.get_prestamos_query import GetPrestamosQueryHandler 

# Commands
from cqrs.commands.financiera.create_asesor_command import CreateAsesorCommand
from cqrs.commands.financiera.update_asesor_command import UpdateAsesorCommand
from cqrs.commands.financiera.create_evaluacion_command import CreateEvaluacionCommand
from cqrs.commands.financiera.update_config_general_command import UpdateConfigGeneralCommand
from cqrs.commands.financiera.create_catalogo_command import CreateCatalogoCommand
from cqrs.commands.financiera.edit_catalogo_command import EditCatalogoCommand
from cqrs.commands.financiera.delete_catalogo_command import DeleteCatalogoCommand
from cqrs.commands.prestamos.create_prestamo_command import CreatePrestamoCommand
from cqrs.commands.prestamos.update_prestamo_command import UpdatePrestamoCommand
# ====================================================================

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

class financieraController:

    # ------------------------------------------------------------
    # DASHBOARD PRINCIPAL (QUERY)
    # ------------------------------------------------------------
    @staticmethod
    def Dashboardfinanciera():
        """Dashboard principal de financiera con estadísticas de cobranza integradas (QUERY)"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "5" or "usuario_id" not in session:
            return redirect(url_for("routes.login2"))
        
        try:
            financiera_id = session.get("usuario_id")
            
            # USANDO QUERY: Reemplaza la lógica de cálculo de KPIs
            stats = GetDashboardQueries.get_finance_kpis(financiera_id)
            
            return render_template(
                "financieras/dashboard.html", 
                usuario=session.get("usuario_nombre"),
                stats=stats
            )
            
        except Exception as e:
            current_app.logger.error(f"Error en dashboard financiera: {e}")
            return "Error al cargar estadísticas", 500
    
    
    # ------------------------------------------------------------
    # CREAR ASESOR (QUERY + COMMAND)
    # ------------------------------------------------------------
    @staticmethod
    def Dashboardasesor_create():
        # 1️⃣ Verificar sesión
        if "usuario_id" not in session:
            return redirect(url_for("routes.login2"))
        
        # 2️⃣ USANDO QUERY: Traer los roles
        try:
            roles = GetAsesorQueries.get_asesor_roles()
            print(roles)
        except Exception as e:
            current_app.logger.error(f"Error al extraer roles: {e}")
            roles = []
            
        # Fecha actual en formato YYYY-MM-DD
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # 3️⃣ Renderizar la plantilla pasando los roles
        return render_template(
            "financieras/asesores/asesor.html",
            roles=roles,
            current_date=current_date
        )
    
    
    @staticmethod
    def create_asesor_post():
        """Ruta para crear un asesor (COMMAND)"""
        # 1️⃣ Verificar sesión
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        # 2️⃣ Obtener datos y validar
        data = request.get_json() if request.is_json else request.form.to_dict()

        required_fields = ["nombre", "apellido", "correo", "contrasena", "tipo_persona"]
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({"error": f"El campo {field} es obligatorio"}), 400

        correo = str(data.get("correo")).strip().lower()
        contrasena = str(data.get("contrasena"))
        rol = str(data.get("tipo_persona")).strip()

        if not EMAIL_REGEX.match(correo):
            return jsonify({"error": "El correo no tiene un formato válido"}), 400
        if len(contrasena) < 8:
            return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400

        # 3️⃣ Generar permisos dinámicos (La lógica se mantiene en el controlador/aplicación)
        permisos_por_rol = {
            "1": { "asesores": {"editar": True, "eliminar": True, "consultas": True}, "clientes": {"editar": True, "eliminar": True, "consultas": True}, "documentos": {"editar": True, "eliminar": True, "consultas": True}, "reportes": {"ver": True, "exportar": True} },
            "2": { "asesores": {"editar": True, "eliminar": False, "consultas": True}, "clientes": {"editar": True, "eliminar": False, "consultas": True}, "documentos": {"editar": True, "eliminar": False, "consultas": True} },
            "3": { "asesores": {"editar": False, "eliminar": False, "consultas": True}, "clientes": {"editar": False, "eliminar": False, "consultas": True}, "documentos": {"editar": False, "eliminar": False, "consultas": True} },
            "4": { "asesores": {"editar": True, "eliminar": True, "consultas": True}, "clientes": {"editar": True, "eliminar": True, "consultas": True}, "documentos": {"editar": True, "eliminar": True, "consultas": True}, "reportes": {"ver": True, "exportar": True} },
            "5": { "asesores": {"editar": True, "eliminar": True, "consultas": True}, "clientes": {"editar": True, "eliminar": True, "consultas": True}, "documentos": {"editar": True, "eliminar": True, "consultas": True}, "reportes": {"ver": True, "exportar": True} },
            "6": { "asesores": {"editar": True, "eliminar": True, "consultas": True}, "clientes": {"editar": True, "eliminar": True, "consultas": True}, "documentos": {"editar": True, "eliminar": True, "consultas": True}, "reportes": {"ver": True, "exportar": True} }
        }
        permisos = permisos_por_rol.get(rol, {})

        # 4️⃣ USANDO COMMAND: Delegar la creación y el hasheo
        try:
            nuevo_id = CreateAsesorCommand(data, permisos).execute()
            return jsonify({"success": True, "usuario_id": nuevo_id}), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 409 # Conflicto de correo
        except Exception as e:
            current_app.logger.error(f"Error al crear asesor: {e}")
            return jsonify({"error": "Error al crear el asesor"}), 500

    @staticmethod
    def get_asesores_data():
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        draw = int(request.args.get("draw", 1))
        start = int(request.args.get("start", 0))
        length = int(request.args.get("length", 10))
        search_value = request.args.get("search[value]", "")
        
        # USANDO QUERY: Delegar la consulta, conteo y resolución de nombres de ubicación
        try:
            resultado = GetAsesorQueries.get_asesores_for_datatable(start, length, search_value)
        except Exception as e:
            current_app.logger.error(f"Error al obtener asesores: {e}")
            return jsonify({"error": "Error al obtener datos de asesores"}), 500

        return jsonify({
            "draw": draw,
            "recordsTotal": resultado["recordsTotal"],
            "recordsFiltered": resultado["recordsFiltered"],
            "data": resultado["data"]
        })


    # ------------------------------------------------------------
    # EDITAR ASESOR (QUERY + COMMAND)
    # ------------------------------------------------------------
    @staticmethod
    def Dashboardasesor_edit():
        # Validar sesión y que sea rol 5
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "5":
            return redirect(url_for("routes.login2"))

        asesor_id = request.args.get("id") or request.form.get("_id")
        if not asesor_id:
            return jsonify({"error": "ID de asesor no proporcionado"}), 400

        try:
            # 🔹 Si es POST, ejecutamos el COMMAND
            if request.method == "POST":
                data = request.form.to_dict()
                # USANDO COMMAND: Actualizar asesor
                result = UpdateAsesorCommand(asesor_id, data).execute()
                
                if result["modified_count"] > 0:
                    flash("Asesor actualizado exitosamente.", "success")
                else:
                    flash("No se realizaron cambios.", "info")
                
                return redirect(url_for("routes.asesores_lista"))

            # 🔹 Si es GET, ejecutamos el QUERY para obtener los datos
            asesor_data = GetAsesorQueries.get_asesor_for_edit_view(asesor_id)
            
            if not asesor_data:
                return jsonify({"error": "Asesor no encontrado o no es rol 3"}), 404
            
            # 🔹 Renderizar plantilla con datos del asesor
            return render_template(
                "financieras/asesores/editar_asesor.html",
                usuario=session.get("usuario_nombre"),
                asesor=asesor_data
            )

        except Exception as e:
            current_app.logger.error(f"Error al cargar/actualizar asesor: {e}")
            flash("Error al procesar la solicitud.", "danger")
            return redirect(url_for("routes.asesores_lista"))

    # ------------------------------------------------------------
    # LISTA ASESORES (VISTA ESTÁTICA)
    # ------------------------------------------------------------
    @staticmethod
    def Dashboardasesor_lista():
        if "usuario_rol" in session and str(session["usuario_rol"]) == "5":
            return render_template("financieras/asesores/lista.html", usuario=session.get("usuario_nombre"))
        return redirect(url_for("routes.login2"))
    
    # ------------------------------------------------------------
    # GESTIÓN DE PRÉSTAMOS (VISTA PRINCIPAL) (QUERY)
    # ------------------------------------------------------------
    @staticmethod
    def Dashboardgestionprestamos():
        # 1. Obtención del ID
        prestamo_id = request.form.get("_id") or request.args.get("_id")

        # Validar sesión
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "5":
            flash("Acceso denegado. Rol de usuario no autorizado.", "danger")
            return redirect(url_for("routes.login2"))
        
        try:
            # USANDO QUERY: Delegar toda la lógica de búsqueda y filtrado
            financieras = GetPrestamoDetailQueries.get_all_financieras_filtered_by_id(prestamo_id)

            if not financieras and not prestamo_id:
                flash("No se encontraron financieras registradas.", "warning")

            # 7. Renderizar el template
            return render_template(
                "financieras/gestion_prestamosf/gestion_prestamos.html",
                usuario=session.get("usuario_nombre"),
                financieras=financieras
            )

        except Exception as ex:
            current_app.logger.error(f"Error inesperado en Dashboardgestionprestamos: {ex}")
            flash("Ocurrió un error inesperado en el sistema.", "danger")
            return render_template(
                "financieras/gestion_prestamosf/gestion_prestamos.html",
                usuario=session.get("usuario_nombre"),
                financieras=[]
            )
    
    # ------------------------------------------------------------
    # GESTIÓN DE PRÉSTAMOS (UPDATE) (QUERY + COMMAND)
    # ------------------------------------------------------------
    @staticmethod
    def Dashboardgestion_prestamos_update():
        prestamo_id = request.form.get("_id") or request.args.get("_id")

        # 1️⃣ Verificar sesión
        if "usuario_id" not in session:
            return jsonify({"status": "error", "message": "Debe iniciar sesión para continuar."}), 401

        # 2️⃣ Validar ID
        if not prestamo_id:
            return jsonify({"status": "error", "message": "ID de prestamo no proporcionado."}), 400

        try:
            # USANDO QUERY (GET): Buscar el prestamo existente (para validación)
            prestamo = GetPrestamoDetailQueries.get_prestamo_by_id(prestamo_id)
            if not prestamo:
                return jsonify({"status": "error", "message": "prestamo no encontrado."}), 404

            # 4️⃣ Si es POST, procesar actualización (COMMAND)
            if request.method == "POST":
                # USANDO COMMAND: Delegar la actualización de la financiera
                result = UpdatePrestamoDetailCommand(prestamo_id, request.form.to_dict(), session.get("usuario_id")).execute() # Asumida
                
                if result["modified_count"] > 0:
                    return jsonify({"status": "success", "message": "prestamo actualizado exitosamente."}), 200
                else:
                    return jsonify({"status": "info", "message": "No se realizaron cambios o los datos ya estaban actualizados."}), 200

            # 6️⃣ Si es GET, devolver el prestamo
            prestamo["_id"] = str(prestamo["_id"])
            return jsonify({"status": "success", "data": prestamo}), 200

        except Exception as e:
            current_app.logger.error(f"Error general en Dashboardgestion_prestamos_update: {e}")
            return jsonify({"status": "error", "message": f"Ocurrió un error: {str(e)}"}), 500
    
    
    # ------------------------------------------------------------
    # REPORTE DE CLIENTES (VISTA Y API) (QUERY)
    # ------------------------------------------------------------
    @staticmethod
    def obtener_conteo_clientes():
        return render_template(
            "financieras/consultas_reportes/consulta_reporte.html", 
            usuario=session.get("usuario_nombre")
        )

    @staticmethod
    def obtener_lista_clientes():
        """Devuelve una lista de diccionarios (los clientes)."""
        # USANDO QUERY: Reemplaza la lógica de búsqueda y serialización
        try:
            return GetAsesorQueries.get_all_clientes_list()
        except Exception as e:
            current_app.logger.error(f"Error al obtener la lista de clientes: {e}")
            return []


    @staticmethod
    def api_conteo_clientes():
        if not ("usuario_rol" in session and str(session["usuario_rol"]) == "5"):
            return jsonify({"status": "error", "message": "Acceso no autorizado"}), 403

        lista_clientes = financieraController.obtener_lista_clientes() 
        
        return jsonify({
            "status": "success",
            "total_clientes": len(lista_clientes),
            "clientes": lista_clientes
        })
    
    # ------------------------------------------------------------
    # EVALUACIÓN DE CRÉDITO (QUERY + COMMAND)
    # ------------------------------------------------------------
    @staticmethod
    def create_evaluacion():
        """Renderiza el formulario para crear una evaluación de crédito (QUERY)"""
        if "usuario_id" not in session:
            return "No autorizado", 401

        try:
            financiera_id = session.get("usuario_id")
            # USANDO QUERY: Obtener clientes de esta financiera
            clientes = GetEvaluacionQueries.get_clients_for_new_evaluation(financiera_id)
        except Exception as e:
            current_app.logger.error(f"Error al extraer clientes para evaluación: {e}")
            clientes = []

        current_date = datetime.now().strftime("%Y-%m-%d")
        
        return render_template(
            "financieras/evaluaciones/crear.html",
            clientes=clientes,
            current_date=current_date
        )
    
    @staticmethod
    def views_evaluaciones():
        """Renderiza la tabla de evaluaciones (usando DataTables)"""
        if "usuario_id" not in session:
            return "No autorizado", 401

        return render_template("financieras/evaluaciones/lista.html")
    
    @staticmethod
    def create_evaluacion_post():
        """Guarda una nueva evaluación de crédito en la base de datos (COMMAND)"""
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        # Obtener datos del formulario
        data = request.get_json() if request.is_json else request.form.to_dict()

        # Validar campos obligatorios (la lógica de validación se mantiene en el controlador)
        required_fields = ["cliente_id", "monto_solicitado", "plazo_meses", "tasa_interes", "proposito_credito"]
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({"error": f"El campo {field} es obligatorio"}), 400

        # USANDO COMMAND: Delegar toda la lógica de cálculo y persistencia
        try:
            financiera_id = session.get("usuario_id")
            evaluacion_id = CreateEvaluacionCommand(data, financiera_id).execute()
            return jsonify({"success": True, "evaluacion_id": evaluacion_id}), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            current_app.logger.error(f"Error al insertar evaluación: {e}")
            return jsonify({"error": "Error al crear la evaluación"}), 500
        
    @staticmethod
    def get_evaluaciones_data():
        """Retorna los datos de evaluaciones en formato DataTables (QUERY)"""
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        draw = int(request.args.get("draw", 1))
        start = int(request.args.get("start", 0))
        length = int(request.args.get("length", 10))
        search_value = request.args.get("search[value]", "")
        financiera_id = session.get("usuario_id")

        # USANDO QUERY: Delegar consulta y conteo
        resultado = GetEvaluacionQueries.get_evaluaciones_for_datatable(financiera_id, start, length, search_value)

        return jsonify({
            "draw": draw,
            "recordsTotal": resultado["recordsTotal"],
            "recordsFiltered": resultado["recordsFiltered"],
            "data": resultado["data"]
        })
    # ------------------------------------------------------------
    # CONFIGURACIÓN (QUERY + COMMANDS)
    # ------------------------------------------------------------
    @staticmethod
    def dashboard_configuracion():
        """Vista principal del módulo de configuración (QUERY)"""
        if "usuario_id" not in session:
            return "No autorizado", 401

        try:
            financiera_id = session.get("usuario_id")
            # USANDO QUERY: Obtener configuración y estadísticas
            config, stats = GetConfigQueries.get_dashboard_config_and_stats(financiera_id)
            
            return render_template(
                "financieras/configuracion/dashboard.html",
                config=config,
                stats=stats
            )
            
        except Exception as e:
            current_app.logger.error(f"Error en dashboard configuración: {e}")
            return "Error al cargar configuración", 500

    @staticmethod
    def configuracion_general():
        """Vista del formulario de configuración general (QUERY)"""
        if "usuario_id" not in session:
            return "No autorizado", 401
        
        try:
            financiera_id = session.get("usuario_id")
            # USANDO QUERY: Obtener configuración actual
            config = GetConfigQueries.get_general_config(financiera_id)
            
            return render_template(
                "financieras/configuracion/general.html",
                config=config
            )
            
        except Exception as e:
            current_app.logger.error(f"Error al cargar configuración: {e}")
            return "Error al cargar configuración", 500

    @staticmethod
    def update_configuracion_general():
        """Actualiza la configuración general (COMMAND)"""
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        try:
            data = request.json
            financiera_id = session.get("usuario_id")
            # USANDO COMMAND: Delegar validación, actualización y auditoría
            result = UpdateConfigGeneralCommand(data, financiera_id, session).execute()
            
            if result["success"]:
                return jsonify({"success": True, "message": "Configuración actualizada correctamente"})
            else:
                return jsonify({"error": "No se pudo actualizar la configuración"}), 500

        except ValueError as e:
            return jsonify({"error": f"Error al procesar los datos: {str(e)}"}), 400
        except Exception as e:
            current_app.logger.error(f"Error al actualizar configuración: {e}")
            return jsonify({"error": f"Error al procesar los datos: {str(e)}"}), 400

    # ------------------------------------------------------------
    # GESTIÓN DE CATÁLOGOS (QUERY + COMMANDS)
    # ------------------------------------------------------------
    @staticmethod
    def catalogos():
        """Vista de gestión de catálogos"""
        if "usuario_id" not in session:
            return "No autorizado", 401

        return render_template("financieras/configuracion/catalogos.html")

    @staticmethod
    def get_catalogos_data():
        """Obtiene datos de catálogos para DataTables (QUERY)"""
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        draw = int(request.args.get("draw", 1))
        start = int(request.args.get("start", 0))
        length = int(request.args.get("length", 10))
        search_value = request.args.get("search[value]", "")
        tipo_filtro = request.args.get("tipo", "")

        # USANDO QUERY: Delegar la consulta
        resultado = GetCatalogoQueries.get_catalogos_for_datatable(start, length, search_value, tipo_filtro)

        return jsonify({
            "draw": draw,
            "recordsTotal": resultado["recordsTotal"],
            "recordsFiltered": resultado["recordsFiltered"],
            "data": resultado["data"]
        })

    @staticmethod
    def create_catalogo():
        """Crea un nuevo elemento de catálogo (COMMAND)"""
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        data = request.json

        # USANDO COMMAND: Delegar la creación y auditoría
        try:
            result = CreateCatalogoCommand(data, session).execute()
            return jsonify({"success": True, "catalogo_id": result["catalogo_id"]}), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            current_app.logger.error(f"Error al crear catálogo: {e}")
            return jsonify({"error": "Error al crear el catálogo"}), 500

    @staticmethod
    def view_catalogo(catalogo_id):
        """Obtiene detalles de un catálogo (QUERY)"""
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        try:
            # USANDO QUERY: Delegar la búsqueda
            catalogo = GetCatalogoQueries.view_catalogo_by_id(catalogo_id)
            
            if catalogo:
                return jsonify(catalogo)

            return jsonify({"error": "Catálogo no encontrado"}), 404
        except Exception as e:
            return jsonify({"error": f"ID inválido: {str(e)}"}), 400

    @staticmethod
    def edit_catalogo(catalogo_id):
        """Actualiza un catálogo (COMMAND)"""
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        data = request.json

        try:
            # USANDO COMMAND: Delegar la actualización y auditoría
            result = EditCatalogoCommand(catalogo_id, data, session).execute()
            
            if result["matched_count"] > 0:
                return jsonify({"success": True})
            else:
                return jsonify({"error": "Catálogo no encontrado"}), 404
        except Exception as e:
            current_app.logger.error(f"Error al editar catálogo: {e}")
            return jsonify({"error": "ID inválido o error de DB"}), 400

    @staticmethod
    def delete_catalogo(catalogo_id):
        """Elimina un catalogo (COMMAND)"""
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        try:
            # USANDO COMMAND: Delegar la eliminación y auditoría
            DeleteCatalogoCommand(catalogo_id, session).execute()
            return jsonify({"success": True})
        except Exception as e:
            current_app.logger.error(f"Error al eliminar catálogo: {e}")
            return jsonify({"error": str(e)}), 500

    # ------------------------------------------------------------
    # AUDITORÍA (QUERY)
    # ------------------------------------------------------------
    @staticmethod
    def auditoria():
        """Vista de auditoria del sistema"""
        if "usuario_id" not in session:
            return "No autorizado", 401

        return render_template("financieras/configuracion/auditoria.html")

    @staticmethod
    def get_auditoria_data():
        """Obtiene datos de auditoria para DataTables (QUERY)"""
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        draw = int(request.args.get("draw", 1))
        start = int(request.args.get("start", 0))
        length = int(request.args.get("length", 10))
        search_value = request.args.get("search[value]", "")

        # USANDO QUERY: Delegar consulta y conteo
        resultado = GetConfigQueries.get_auditoria_for_datatable(start, length, search_value)

        return jsonify({
            "draw": draw,
            "recordsTotal": resultado["recordsTotal"],
            "recordsFiltered": resultado["recordsFiltered"],
            "data": resultado["data"]
        })

    @staticmethod
    def view_auditoria(auditoria_id):
        """Obtiene detalles de un registro de auditoría (QUERY)"""
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        try:
            # USANDO QUERY: Delegar la búsqueda
            auditoria = GetConfigQueries.view_auditoria_by_id(auditoria_id)
            
            if auditoria:
                return jsonify(auditoria)

            return jsonify({"error": "Registro no encontrado"}), 404
        except Exception:
            return jsonify({"error": "ID invalido"}), 400

    # ------------------------------------------------------------
    # PROYECCIONES (VISTAS ESTÁTICAS Y API)
    # ------------------------------------------------------------
    @staticmethod
    def proyeccion_liquidados():
        return render_template("financieras/proyeccion/proyeccion_liquidados.html")

    @staticmethod
    def proyeccion_mora():
        return render_template("financieras/proyeccion/proyeccion_mora.html")

    @staticmethod
    def proyeccion_pagos():
        return render_template("financieras/proyeccion/proyeccion_pagos.html")
    
    @staticmethod
    def proyeccion_prestamos():
        return render_template("financieras/proyeccion/proyeccion_prestamos.html")

    @staticmethod
    def api_reporte_liquidaciones():
        """API para obtener datos de liquidaciones (QUERY)"""
        try:
            fecha_inicio_str = request.args.get("inicio")
            fecha_fin_str = request.args.get("fin")

            if not fecha_inicio_str or not fecha_fin_str:
                return jsonify({"error": "Fechas de inicio y fin son requeridas"}), 400

            # USANDO QUERY: Delegar la lógica compleja de búsqueda, join, cálculo de KPIs y formato de gráfico
            return GetProyeccionQueries.get_liquidaciones_report(fecha_inicio_str, fecha_fin_str)

        except Exception as e:
            current_app.logger.error(f"Error en api_reporte_liquidaciones: {e}", exc_info=True)
            return jsonify({"error": f"Error interno: {str(e)}"}), 500
    
    @staticmethod
    def api_reporte_mora():
        """API para obtener datos de mora proyectada (QUERY)"""
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401
        financiera_id = session.get("usuario_id")
        
        # USANDO QUERY: Delegar la búsqueda
        try:
            data = GetProyeccionQueries.get_mora_data(financiera_id)
            return jsonify({"success": True, "data": data})
        except Exception as e:
            current_app.logger.error(f"Error al obtener mora: {e}")
            return jsonify({"error": "Error al obtener los datos"}), 500
        
    @staticmethod
    def api_reporte_pagos():
        """API para obtener datos de pagos proyectados (QUERY)"""
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401
        financiera_id = session.get("usuario_id")

        # USANDO QUERY: Delegar la búsqueda
        try:
            data = GetProyeccionQueries.get_pagos_data(financiera_id)
            return jsonify({"success": True, "data": data})
        except Exception as e:
            current_app.logger.error(f"Error al obtener pagos: {e}")
            return jsonify({"error": "Error al obtener los datos"}), 500
    
    @staticmethod
    def api_reporte_prestamos():
        """API para obtener datos de préstamos proyectados (QUERY)"""
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401
        financiera_id = session.get("usuario_id")

        # USANDO QUERY: Delegar la búsqueda
        try:
            data = GetProyeccionQueries.get_prestamos_data(financiera_id)
            return jsonify({"success": True, "data": data})
        except Exception as e:
            current_app.logger.error(f"Error al obtener préstamos: {e}")
            return jsonify({"error": "Error al obtener los datos"}), 500
    
    # ------------------------------------------------------------
    # GESTIÓN DE PRÉSTAMOS (VISTAS Y DATA TABLES)
    # ------------------------------------------------------------
    @staticmethod
    def view_prestamos_lista():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login2"))
        return render_template("financieras/gestion_prestamo/gestion_prestamos.html", usuario=session.get("usuario_nombre"))

    @staticmethod
    def get_prestamos_data():
        # 1. Verificación de Sesión
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        # Parámetros de DataTables
        draw = int(request.args.get("draw", 1))
        start = int(request.args.get("start", 0))
        length = int(request.args.get("length", 10))
        search_value = request.args.get("search[value]", "")

        # Obtener financiera_id (lógica mantenida aquí por dependencia de sesión)
        usuario_id = session["usuario_id"]
        financiera_id = None

        try:
            usuario_data = db.usuarios.find_one({"_id": ObjectId(usuario_id)})
            if usuario_data:
                financiera_id = usuario_data.get("usuario_idFinanciera", None)
        except Exception as e:
            current_app.logger.error(f"Error buscando usuario: {e}")

        # USANDO QUERY HANDLER: Delegar la consulta
        query_handler = GetPrestamosQueryHandler()
        
        resultado = query_handler.handle(
            financiera_id=financiera_id,
            start=start,
            length=length,
            search_value=search_value
        )

        # Responder JSON
        return jsonify({
            "draw": draw,
            "recordsTotal": resultado["recordsTotal"],
            "recordsFiltered": resultado["recordsFiltered"],
            "data": resultado["data"]
        })

    @staticmethod
    def view_prestamo_crear():
        if "usuario_id" not in session:
            return redirect(url_for("routes.login2"))
        
        # USANDO QUERY: Obtener clientes (filtrado por financiera)
        financiera_id = session.get("usuario_id")
        clientes = GetEvaluacionQueries.get_clients_for_new_evaluation(financiera_id)
        
        return render_template("financieras/gestion_prestamo/crear_prestamo.html", clientes=clientes, usuario=session.get("usuario_nombre"))

    @staticmethod
    def store_prestamo():
        if "usuario_id" not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401

        data = request.form
        cliente_id = data.get("cliente_id")
        
        if not cliente_id:
            return jsonify({"status": "error", "message": "El cliente es obligatorio"}), 400

        try:
            # USANDO COMMAND: Delegar la creación
            CreatePrestamoCommand(data, session.get("usuario_id")).execute()
            return jsonify({"status": "success", "message": "Préstamo creado correctamente"})
            
        except Exception as e:
            current_app.logger.error(f"Error store: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @staticmethod
    def view_prestamo_detalle(id_prestamo):
        if "usuario_id" not in session:
            return redirect(url_for("routes.login2"))

        # USANDO QUERY: Delegar la búsqueda y el join con cliente
        prestamo = GetPrestamoDetailQueries.get_prestamo_detail(id_prestamo)
        if not prestamo:
            return redirect(url_for("routes.prestamos_lista"))
        
        return render_template("financieras/gestion_prestamo/ver_gestion_prestamos.html", prestamo=prestamo, usuario=session.get("usuario_nombre"))

    @staticmethod
    def view_prestamo_editar(id_prestamo):
        if "usuario_id" not in session:
            return redirect(url_for("routes.login2"))

        # USANDO QUERY: Delegar la búsqueda y el join con cliente
        prestamo = GetPrestamoDetailQueries.get_prestamo_detail(id_prestamo)
        if not prestamo:
            return redirect(url_for("routes.prestamos_lista"))

        estados = ["Pendiente", "Aprobado", "Pagado", "Mora", "Cancelado"]
        
        return render_template("financieras/gestion_prestamo/editar_gestion_prestamos.html", prestamo=prestamo, estados=estados, usuario=session.get("usuario_nombre"))

    @staticmethod
    def update_prestamo():
        if "usuario_id" not in session:
            return jsonify({"status": "error"}), 401
        
        data = request.form
        prestamo_id = data.get("_id")
        
        try:
            # USANDO COMMAND: Delegar la actualización
            UpdatePrestamoCommand(prestamo_id, data, session.get("usuario_id")).execute()
            return jsonify({"status": "success", "message": "Actualizado correctamente"})
        except Exception as e:
            current_app.logger.error(f"Error al actualizar préstamo: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
        
    @staticmethod
    def listar_clientes_financiera():
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "5":
            return redirect(url_for("routes.login2"))
        
        # Obtenemos la lista de asesores activos para el modal de reasignación
        financiera_id = session.get("usuario_id")
        asesores = list(db.usuarios.find({"usuario_idFinanciera": financiera_id, "usuario_rol": "3"}))
        
        return render_template("financieras/cliente/lista_clientes.html", 
                            usuario=session.get("usuario_nombre"),
                            asesores=asesores)

    @staticmethod
    def get_clientes_financiera_data():
        financiera_id = session.get("usuario_id")
        # Simulación de Query para obtener clientes con su asesor ligado
        clientes = list(db.clientes.find({"cliente_idFinanciera": financiera_id}))
        
        data = []
        for c in clientes:
            # Buscamos info del asesor ligado
            asesor = db.usuarios.find_one({"_id": ObjectId(c.get("cliente_idAsesor"))}) if c.get("cliente_idAsesor") else None
            
            data.append({
                "_id": str(c["_id"]),
                "nombre": f"{c.get('cliente_nombre')} {c.get('cliente_apellidos')}",
                "email": c.get("cliente_email"),
                "status_docs": c.get("cliente_status_documentos", "Pendiente"),
                "asesor_nombre": f"{asesor['usuario_nombre']} {asesor['usuario_apellidos']}" if asesor else "Sin asignar",
                "asesor_id": str(asesor["_id"]) if asesor else ""
            })
        return jsonify({"data": data})
    
    @staticmethod
    def asignar_asesor_cliente():
        """
        Permite a la financiera asignar o cambiar el asesor de un cliente (COMMAND)
        """
        # 1. Verificar sesión y rol de financiera (rol 5)
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "5":
            return jsonify({"status": "error", "message": "No autorizado"}), 401

        try:
            # 2. Obtener datos de la petición
            data = request.get_json() if request.is_json else request.form.to_dict()
            cliente_id = data.get("cliente_id")
            nuevo_asesor_id = data.get("asesor_id")

            if not cliente_id or not nuevo_asesor_id:
                return jsonify({"status": "error", "message": "Datos incompletos"}), 400

            # 3. Actualizar el campo cliente_idAsesor en la colección de clientes
            # Utilizamos la referencia a la base de datos configurada en el proyecto
            result = db.clientes.update_one(
                {"_id": ObjectId(cliente_id)},
                {"$set": {
                    "cliente_idAsesor": ObjectId(nuevo_asesor_id),
                    "updated_at": datetime.utcnow()
                }}
            )

            if result.modified_count > 0:
                # Opcional: Registrar en auditoría si el sistema lo requiere
                return jsonify({"status": "success", "message": "Asesor asignado correctamente"}), 200
            else:
                return jsonify({"status": "info", "message": "El cliente ya tiene asignado ese asesor"}), 200

        except Exception as e:
            current_app.logger.error(f"Error al asignar asesor: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
        
    @staticmethod
    def get_clientes_financiera_data():
        if "usuario_id" not in session:
            return jsonify({"error": "No autorizado"}), 401

        financiera_id = session.get("usuario_id")
        
        try:
            # Buscamos clientes ligados a esta financiera
            clientes = list(db.clientes.find({"cliente_idFinanciera": financiera_id}))
            
            data = []
            for c in clientes:
                # Obtener info del asesor
                asesor_info = "Sin asignar"
                if c.get("cliente_idAsesor"):
                    asesor = db.usuarios.find_one({"_id": ObjectId(c["cliente_idAsesor"])})
                    if asesor:
                        asesor_info = f"{asesor.get('usuario_nombre')} {asesor.get('usuario_apellidos')}"

                # Simulación de conteo de documentos subidos
                # En un entorno real, contarías archivos en la carpeta del cliente o en la DB de documentos
                docs_count = db.documentos.count_documents({"cliente_id": c["_id"]})

                data.append({
                    "_id": str(c["_id"]),
                    "nombre": f"{c.get('cliente_nombre', '')} {c.get('cliente_apellidos', '')}",
                    "email": c.get("cliente_email", "N/A"),
                    "asesor_nombre": asesor_info,
                    "asesor_id": str(c.get("cliente_idAsesor", "")),
                    "status_docs": c.get("cliente_status_documentos", "Pendiente"),
                    "docs_count": docs_count,
                    # Información no sensible para evaluación rápida
                    "tipo_persona": c.get("cliente_persona", "No definido"),
                    "registro": c.get("created_at").strftime("%Y-%m-%d") if c.get("created_at") else "N/A"
                })

            return jsonify({"data": data})
        except Exception as e:
            current_app.logger.error(f"Error data clientes: {e}")
            return jsonify({"data": []}), 500