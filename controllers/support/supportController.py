from flask import render_template, request, jsonify, session, redirect, url_for
from config.db import db
from bson.objectid import ObjectId
from datetime import datetime, timedelta


class supportController:
    #   DASHBOARD PRINCIPAL
    @staticmethod
    def Dashboardsoporte():
        """Renderiza el dashboard principal"""
        try:
            if "usuario_rol" in session and str(session["usuario_rol"]) == "6":
                return render_template("support/dashboard.html")
            return redirect(url_for("routes.login"))
        except Exception as e:
            print(f"Error en Dashboardsoporte: {e}")
            return render_template("support/dashboard.html")


    @staticmethod
    def DashboardData():
        """API que devuelve los datos del dashboard"""
        try:
            print("\n" + "="*50)
            print("INICIANDO DashboardData...")
            print("="*50)
            
            # === CONTADORES PRINCIPALES ===
            total = db.tickets.count_documents({})
            print(f"Total de tickets: {total}")
            
            abiertos = db.tickets.count_documents({"estado": {"$in": ["Abierto", "abierto", "pendiente", "Pendiente"]}})
            cerrados = db.tickets.count_documents({"estado": {"$in": ["Cerrado", "cerrado", "resuelto", "Resuelto"]}})
            criticos = db.tickets.count_documents({"prioridad": {"$in": ["Alta", "alta", "critica", "crítica"]}})

            print(f"CONTADORES:")
            print(f"   Total: {total}")
            print(f"   Abiertos: {abiertos}")
            print(f"   Cerrados: {cerrados}")
            print(f"   Críticos: {criticos}")

            # === AGRUPACIÓN POR ESTADO ===
            try:
                pipeline_estados = [
                    {
                        "$group": {
                            "_id": "$estado",
                            "cantidad": {"$sum": 1}
                        }
                    },
                    {"$sort": {"cantidad": -1}}
                ]

                estados_raw = list(db.tickets.aggregate(pipeline_estados))
                datos_estados = []
                
                for e in estados_raw:
                    estado_nombre = e.get("_id")
                    if estado_nombre:
                        datos_estados.append({
                            "estado": str(estado_nombre),
                            "cantidad": e["cantidad"]
                        })
                
                if not datos_estados:
                    datos_estados = [{"estado": "Sin datos", "cantidad": 0}]
                    
                print(f"ESTADOS: {datos_estados}")
            except Exception as e:
                print(f"Error en agregación de estados: {e}")
                datos_estados = [{"estado": "Error", "cantidad": 0}]

            # === EVOLUCIÓN TEMPORAL ===
            datos_evolucion = []
            try:
                ahora = datetime.now()
                hace_6_meses = ahora - timedelta(days=180)

                ticket_sample = db.tickets.find_one()
                print(f"Ticket de ejemplo: {ticket_sample}")
                
                if ticket_sample and "fecha" in ticket_sample:
                    pipeline_evolucion = [
                        {
                            "$match": {
                                "fecha": {"$gte": hace_6_meses, "$exists": True, "$ne": None}
                            }
                        },
                        {
                            "$group": {
                                "_id": {
                                    "$dateToString": {
                                        "format": "%Y-%m",
                                        "date": "$fecha"
                                    }
                                },
                                "cantidad": {"$sum": 1}
                            }
                        },
                        {"$sort": {"_id": 1}}
                    ]

                    evolucion_raw = list(db.tickets.aggregate(pipeline_evolucion))
                    
                    meses_es = {
                        "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr",
                        "05": "May", "06": "Jun", "07": "Jul", "08": "Ago",
                        "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic"
                    }
                    
                    for e in evolucion_raw:
                        try:
                            año, mes = e["_id"].split("-")
                            mes_nombre = f"{meses_es.get(mes, mes)} {año[-2:]}"
                            datos_evolucion.append({
                                "mes": mes_nombre,
                                "cantidad": e["cantidad"]
                            })
                        except:
                            datos_evolucion.append({
                                "mes": str(e.get("_id", "N/A")),
                                "cantidad": e["cantidad"]
                            })
                else:
                    print("No hay campo 'fecha' en los tickets")
                    datos_evolucion = []
                
                print(f"EVOLUCIÓN: {datos_evolucion}")
            except Exception as e:
                print(f"Error en evolución temporal: {e}")
                datos_evolucion = []

            # === ALERTAS ===
            alertas = []
            try:
                alertas_cursor = db.tickets.find({
                    "estado": {"$in": ["Abierto", "abierto", "pendiente", "Pendiente", "en_revision"]}
                }).sort("_id", -1).limit(5)

                for a in alertas_cursor:
                    usuario_nombre = "Sin cliente"
                    if a.get("usuario_id"):
                        try:
                            from bson.objectid import ObjectId
                            usuario = db.usuarios.find_one({"_id": ObjectId(a["usuario_id"])})
                            if usuario:
                                usuario_nombre = f"{usuario.get('usuario_nombre', '')} {usuario.get('usuario_apellidos', '')}".strip()
                        except:
                            pass
                    
                    alerta_data = {
                        "_id": str(a["_id"]),
                        "estado": a.get("estado", "N/A"),
                        "titulo": a.get("asunto") or a.get("titulo") or a.get("tipo") or f"Ticket #{str(a['_id'])[-6:]}",
                        "cliente": usuario_nombre
                    }
                    
                    if "fecha" in a and isinstance(a["fecha"], datetime):
                        alerta_data["fecha_creacion"] = a["fecha"].strftime("%d/%m/%Y %H:%M")
                    else:
                        alerta_data["fecha_creacion"] = "N/A"
                    
                    alertas.append(alerta_data)

                print(f"ALERTAS: {len(alertas)} encontradas")
            except Exception as e:
                print(f"Error en alertas: {e}")
                alertas = []

            # === ÚLTIMOS TICKETS ===
            ultimos = []
            try:
                tickets_cursor = db.tickets.find().sort("_id", -1).limit(10)
                
                for t in tickets_cursor:
                    usuario_nombre = "Sin especificar"
                    if t.get("usuario_id"):
                        try:
                            from bson.objectid import ObjectId
                            usuario = db.usuarios.find_one({"_id": ObjectId(t["usuario_id"])})
                            if usuario:
                                usuario_nombre = f"{usuario.get('usuario_nombre', '')} {usuario.get('usuario_apellidos', '')}".strip()
                        except:
                            pass
                    
                    ticket_data = {
                        "_id": str(t["_id"]),
                        "cliente": usuario_nombre,
                        "tipo": t.get("asunto") or t.get("tipo") or "General",
                        "estado": t.get("estado", "pendiente"),
                        "prioridad": t.get("prioridad", "media"),
                        "asignado_a": t.get("asesor") or "Sin asignar"
                    }
                    
                    if "fecha" in t and isinstance(t["fecha"], datetime):
                        ticket_data["fecha_creacion"] = t["fecha"].strftime("%d/%m/%Y %H:%M")
                    else:
                        ticket_data["fecha_creacion"] = "N/A"
                    
                    ultimos.append(ticket_data)

                print(f"TICKETS: {len(ultimos)} recientes")
            except Exception as e:
                print(f"Error en últimos tickets: {e}")
                ultimos = []

            # === RESPUESTA FINAL ===
            respuesta = {
                "resumen": {
                    "total": total,
                    "abiertos": abiertos,
                    "cerrados": cerrados,
                    "criticos": criticos
                },
                "estados": datos_estados,
                "evolucion": datos_evolucion,
                "alertas": alertas,
                "tickets": ultimos
            }

            print("DashboardData completado exitosamente")
            print("="*50 + "\n")
            return jsonify(respuesta)

        except Exception as e:
            print(f"ERROR CRÍTICO en DashboardData: {e}")
            import traceback
            traceback.print_exc()
            
            return jsonify({
                "resumen": {"total": 0, "abiertos": 0, "cerrados": 0, "criticos": 0},
                "estados": [{"estado": "Error", "cantidad": 0}],
                "evolucion": [],
                "alertas": [],
                "tickets": [],
                "error": str(e)
            }), 200


    #   CHAT FAQ
    @staticmethod
    def ChatFAQ():
        """Renderiza la página de comunicación con FAQ"""
        try:
            if "usuario_rol" in session and str(session["usuario_rol"]) == "6":
                # Verificar qué archivo existe
                try:
                    return render_template("support/comunicacion.html")
                except:
                    return render_template("support/comunicacion_ticket.html")
            return redirect(url_for("routes.login"))
        except Exception as e:
            print(f"Error en ChatFAQ: {e}")
            import traceback
            traceback.print_exc()
            # Intentar ambos nombres
            try:
                return render_template("support/comunicacion.html")
            except:
                return render_template("support/comunicacion_ticket.html")


    @staticmethod
    def ProcesarPreguntaFAQ():
        """Procesa preguntas del chat FAQ"""
        try:
            data = request.get_json()
            pregunta = data.get("pregunta", "").lower().strip()
            
            respuestas = {
                "horario": {
                    "keywords": ["horario", "hora", "atención", "atencion"],
                    "respuesta": "⏰ Nuestro horario es Lunes a Viernes 9AM-6PM, Sábados 9AM-2PM"
                },
                "ticket": {
                    "keywords": ["ticket", "seguimiento", "estado"],
                    "respuesta": "🎫 Puedes consultar tu ticket en 'Mis Tickets' con tu número de referencia"
                },
                "contacto": {
                    "keywords": ["contacto", "whatsapp", "teléfono", "telefono"],
                    "respuesta": "📞 WhatsApp: +52 722 123 4567 | Email: soporte@tuempresa.com",
                    "necesita_humano": True
                }
            }
            
            for categoria, info in respuestas.items():
                if any(kw in pregunta for kw in info["keywords"]):
                    return jsonify({
                        "respuesta": info["respuesta"],
                        "necesita_humano": info.get("necesita_humano", False)
                    })
            
            return jsonify({
                "respuesta": "🤔 No tengo una respuesta específica. ¿Te conecto con un asesor?",
                "necesita_humano": True
            })
            
        except Exception as e:
            print(f"Error en ProcesarPreguntaFAQ: {e}")
            return jsonify({"error": str(e)}), 500


    #   TICKETS ACTIVOS
    @staticmethod
    def TicketsActivos():
        """Muestra todos los tickets con filtros"""
        try:
            tickets = []
            tickets_cursor = db.tickets.find().sort("_id", -1)

            for t in tickets_cursor:
                # Obtener nombre del usuario
                usuario_nombre = "Sin nombre"
                if t.get("usuario_id"):
                    try:
                        usuario = db.usuarios.find_one({"_id": ObjectId(t["usuario_id"])})
                        if usuario:
                            usuario_nombre = f"{usuario.get('usuario_nombre', '')} {usuario.get('usuario_apellidos', '')}".strip()
                    except:
                        pass
                
                tickets.append({
                    "id": str(t["_id"]),
                    "cliente_nombre": usuario_nombre,
                    "tipo_incidencia": t.get("asunto", "No especificado"),
                    "estado": t.get("estado", "pendiente"),
                    "prioridad": t.get("prioridad", "media"),
                    "fecha_creacion": t["fecha"].strftime("%Y-%m-%d %H:%M") if isinstance(t.get("fecha"), datetime) else "N/A",
                    "ultima_actualizacion": t["ultima_actualizacion"].strftime("%Y-%m-%d %H:%M") if isinstance(t.get("ultima_actualizacion"), datetime) else "N/A",
                })

            return render_template("support/tickets.html", tickets=tickets)

        except Exception as e:
            print(f"Error al cargar tickets: {e}")
            import traceback
            traceback.print_exc()
            return render_template("support/tickets.html", tickets=[], error=str(e))


    #   ALERTAS
    @staticmethod
    def AlertasSoporte():
        """Muestra alertas de tickets pendientes"""
        try:
            print("Cargando alertas...")
            
            alertas = list(db.tickets.find({
                "estado": {"$in": ["Abierto", "abierto", "pendiente", "Pendiente", "en_revision", "en revisión", "En revisión"]}
            }).sort("_id", -1).limit(100))

            print(f"Total de tickets encontrados: {len(alertas)}")

            for a in alertas:
                a["_id"] = str(a["_id"])
                
                # Obtener nombre del usuario
                usuario_nombre = "Sin cliente"
                if a.get("usuario_id"):
                    try:
                        usuario = db.usuarios.find_one({"_id": ObjectId(a["usuario_id"])})
                        if usuario:
                            usuario_nombre = f"{usuario.get('usuario_nombre', '')} {usuario.get('usuario_apellidos', '')}".strip()
                    except:
                        pass
                
                # Usar 'fecha' y 'asunto'
                if isinstance(a.get("fecha"), datetime):
                    a["fecha_creacion"] = a["fecha"].strftime("%Y-%m-%d %H:%M")
                else:
                    a["fecha_creacion"] = "N/A"
                
                a["cliente"] = usuario_nombre
                a["cliente_nombre"] = usuario_nombre
                a["titulo"] = a.get("asunto", "Ticket sin título")
                a["estado"] = a.get("estado", "pendiente").lower().replace(" ", "_")
                a["prioridad"] = a.get("prioridad", "media").lower()
                a["asignado_a"] = a.get("asesor", "")
                a["descripcion"] = a.get("descripcion", "")

            print(f"Alertas procesadas: {len(alertas)}")
            if alertas:
                print(f"Ejemplo de alerta: {alertas[0]}")

            return render_template("support/alertas.html", alertas=alertas)

        except Exception as e:
            print(f"Error en AlertasSoporte: {e}")
            import traceback
            traceback.print_exc()
            return render_template("support/alertas.html", alertas=[], error=str(e))


    #   HISTORIAL
    @staticmethod
    def HistorialSoporte():
        """Muestra historial de tickets cerrados"""
        try:
            print("Cargando historial...")
            
            # Obtener tickets cerrados/resueltos
            historial = list(db.tickets.find({
                "estado": {"$in": ["Cerrado", "cerrado", "resuelto", "Resuelto", "completado", "Completado"]}
            }).sort("_id", -1).limit(200))

            print(f"Tickets cerrados encontrados: {len(historial)}")

            for h in historial:
                h["_id"] = str(h["_id"])
                
                # Formatear fecha
                if isinstance(h.get("fecha_creacion"), datetime):
                    h["fecha_creacion"] = h["fecha_creacion"].strftime("%Y-%m-%d %H:%M")
                elif h.get("fecha_creacion"):
                    pass  
                else:
                    h["fecha_creacion"] = "N/A"
                
                # Asegurar campos mínimos
                h["cliente_nombre"] = h.get("cliente") or h.get("cliente_nombre", "Sin nombre")
                h["tipo_incidencia"] = h.get("tipo") or h.get("tipo_incidencia", "No especificado")
                h["estado"] = h.get("estado", "cerrado")
                h["prioridad"] = h.get("prioridad", "")
                h["asesor"] = h.get("asesor") or h.get("asignado_a", "")
                h["descripcion"] = h.get("descripcion") or h.get("detalle", "")

            print(f"Historial procesado: {len(historial)} tickets")

            return render_template("support/historial.html", historial=historial)

        except Exception as e:
            print(f"Error en HistorialSoporte: {e}")
            import traceback
            traceback.print_exc()
            return render_template("support/historial.html", historial=[], error=str(e))


    #   MÉTRICAS
    @staticmethod
    def MetricasSoporte():
        """Dashboard de métricas avanzadas"""
        try:
            total_tickets = db.tickets.count_documents({})
            abiertos = db.tickets.count_documents({"estado": {"$in": ["Abierto", "abierto", "pendiente"]}})
            cerrados = db.tickets.count_documents({"estado": {"$in": ["Cerrado", "cerrado", "resuelto"]}})
            criticos = db.tickets.count_documents({"prioridad": {"$in": ["Alta", "alta", "critica"]}})

            datos = {
                "resumen": {
                    "total": total_tickets,
                    "abiertos": abiertos,
                    "cerrados": cerrados,
                    "criticos": criticos
                },
                "tipos": {},
                "tiempos": {},
                "resueltos": {},
                "criticas": {"criticas": 0, "normales": 100}
            }

            return render_template("support/metricas.html", datos=datos)

        except Exception as e:
            print(f"Error en MetricasSoporte: {e}")
            return render_template("support/metricas.html", error=str(e))


    #   GESTIÓN DE EQUIPO
    @staticmethod
    def GestionEquipo():
        """Gestión de asignación de tickets"""
        try:
            print("Cargando gestión de equipo...")
            
            # Obtener asesores INTERNOS
            asesores_cursor = db.usuarios.find(
                {
                    "usuario_tipo_asesor": "interno",
                    "usuario_status": 1
                },
                {
                    "_id": 1, 
                    "usuario_nombre": 1, 
                    "usuario_apellidos": 1,
                    "usuario_email": 1
                }
            ).sort("usuario_nombre", 1)

            asesores = []
            for a in asesores_cursor:
                nombre_completo = f"{a.get('usuario_nombre', '')} {a.get('usuario_apellidos', '')}".strip()
                if nombre_completo:
                    asesores.append({
                        "id": str(a["_id"]),
                        "nombre": nombre_completo,
                        "email": a.get("usuario_email", "Sin email")
                    })

            print(f"👥 Asesores encontrados: {len(asesores)}")

            # Obtener tickets activos
            tickets = []
            tickets_cursor = db.tickets.find({
                "estado": {"$nin": ["cerrado", "Cerrado", "resuelto", "Resuelto"]}
            }).sort("_id", -1).limit(50)

            for t in tickets_cursor:
                # Obtener nombre del usuario
                usuario_nombre = "Sin nombre"
                if t.get("usuario_id"):
                    try:
                        usuario = db.usuarios.find_one({"_id": ObjectId(t["usuario_id"])})
                        if usuario:
                            usuario_nombre = f"{usuario.get('usuario_nombre', '')} {usuario.get('usuario_apellidos', '')}".strip()
                    except:
                        pass
                
                tickets.append({
                    "id": str(t["_id"]),
                    "cliente_nombre": usuario_nombre,
                    "asesor": t.get("asesor", ""),
                    "area": t.get("asunto", "general"),
                    "estado": t.get("estado", "pendiente")
                })

            print(f"Tickets activos: {len(tickets)}")

            return render_template("support/gestion.html", tickets=tickets, asesores=asesores)

        except Exception as e:
            print(f"Error en GestionEquipo: {e}")
            import traceback
            traceback.print_exc()
            return render_template("support/gestion.html", tickets=[], asesores=[], error=str(e))


    #   ACTUALIZAR TICKET
    @staticmethod
    def ActualizarTicket():
        """API para actualizar un ticket"""
        try:
            data = request.get_json()
            ticket_id = data.get("id") or data.get("ticket_id")
            
            if not ticket_id:
                return jsonify({"error": "ID de ticket requerido"}), 400

            update_fields = {}
            
            if "estado" in data:
                update_fields["estado"] = data["estado"]
            if "prioridad" in data:
                update_fields["prioridad"] = data["prioridad"]
            if "asesor" in data:
                update_fields["asesor"] = data["asesor"]
            if "asignado_a" in data:
                update_fields["asignado_a"] = data["asignado_a"]
            
            update_fields["ultima_actualizacion"] = datetime.now()

            resultado = db.tickets.update_one(
                {"_id": ObjectId(ticket_id)},
                {"$set": update_fields}
            )

            if resultado.modified_count > 0:
                return jsonify({"success": True, "mensaje": "Ticket actualizado"})
            else:
                return jsonify({"success": False, "mensaje": "No se realizaron cambios"})

        except Exception as e:
            print(f"Error en ActualizarTicket: {e}")
            return jsonify({"error": str(e)}), 500


    #   ALIAS (COMPATIBILIDAD)
    @staticmethod
    def ApiDashboardSoporte():
        """Alias para DashboardData"""
        return supportController.DashboardData()