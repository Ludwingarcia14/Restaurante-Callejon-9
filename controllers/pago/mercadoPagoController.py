import os
import mercadopago
from flask import jsonify, request, redirect, url_for, session
from config.db import db
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv
from models.ticket_model import Ticket

load_dotenv()

# Inicializa SDK
sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

class MercadoPagoController:

    @staticmethod
    def crear_preferencia(cuenta_id):
        """Crea una preferencia de pago en Mercado Pago"""
        
        data = request.get_json() or {}
        tipo_propina = data.get("tipo_propina", "sin")
        custom_porcentaje = data.get("custom_porcentaje")
        
        comanda = db.comandas.find_one({"_id": cuenta_id})
        if not comanda:
            return jsonify({
                "success": False,
                "error": "Cuenta no encontrada"
            }), 404

        total = float(comanda.get("total", 0))
        
        # Calcular propina
        propina = 0
        porcentaje_propina = 0
        
        if tipo_propina == "custom" and custom_porcentaje:
            porcentaje_propina = float(custom_porcentaje)
        elif tipo_propina in ["10", "15", "20"]:
            porcentaje_propina = float(tipo_propina)
        
        if porcentaje_propina > 0:
            propina = total * (porcentaje_propina / 100)
        
        total_final = total + propina

        if total_final <= 0:
            return jsonify({
                "success": False,
                "error": "El total debe ser mayor a 0"
            }), 400

        # 🔥 PREFERENCIA SIN BACK_URLS (sin túnel)
        preference_data = {
            "items": [
                {
                    "title": f"Mesa {comanda.get('mesa_numero')} - {comanda.get('folio', 'Cuenta')}",
                    "description": f"Consumo: ${total:.2f} + Propina ({porcentaje_propina}%): ${propina:.2f}",
                    "quantity": 1,
                    "currency_id": "MXN",
                    "unit_price": float(total_final)
                }
            ],
            "external_reference": str(cuenta_id),
            "statement_descriptor": "RESTAURANTE",
            "metadata": {
                "cuenta_id": str(cuenta_id),
                "mesa_numero": comanda.get('mesa_numero'),
                "propina": float(propina),
                "porcentaje_propina": porcentaje_propina,
                "mesero_id": str(comanda.get('mesero_id', ''))
            }
        }

        result = sdk.preference().create(preference_data)

        if result["status"] not in [200, 201]:
            return jsonify({
                "success": False,
                "error": result.get("response", {}).get("message", "Error al crear preferencia")
            }), 400

        preference = result["response"]
        
        # 🔥 USA SANDBOX EN DESARROLLO
        init_point = preference.get("sandbox_init_point") or preference.get("init_point")
        preference_id = preference.get("id")

        # 🔥 GUARDAR PREFERENCIA EN BD
        db.payment_preferences.insert_one({
            "preference_id": preference_id,
            "cuenta_id": str(cuenta_id),
            "total": total_final,
            "propina": propina,
            "porcentaje_propina": porcentaje_propina,
            "status": "pending",
            "created_at": datetime.now()
        })

        return jsonify({
            "success": True,
            "init_point": init_point,
            "preference_id": preference_id
        })

    @staticmethod
    def verificar_pago_mercadopago(cuenta_id):
        """
        🔥 VERIFICA EL ESTADO DEL PAGO DIRECTAMENTE CON MERCADO PAGO
        """
        try:
            cuenta_oid = ObjectId(cuenta_id)
        except:
            return jsonify({
                "success": False,
                "error": "ID inválido"
            }), 400
        
        # 1. Verificar si ya está cerrada en nuestra BD
        comanda = db.comandas.find_one({"_id": cuenta_oid})
        
        if not comanda:
            return jsonify({
                "success": False,
                "error": "Comanda no encontrada"
            }), 404
        
        # Si ya está cerrada, retornar el estado
        if comanda.get("estado") in ["cerrada", "pagada"]:
            return jsonify({
                "success": True,
                "status": "approved",
                "total": float(comanda.get("total_final", comanda.get("total", 0))),
                "propina": float(comanda.get("propina", 0)),
                "metodo_pago": comanda.get("metodo_pago", "mercadopago")
            })
        
        # 2. 🔥 BUSCAR LA PREFERENCIA EN BD
        preference = db.payment_preferences.find_one({"cuenta_id": str(cuenta_id)})
        
        if not preference:
            return jsonify({
                "success": True,
                "status": "pending",
                "message": "No hay pago iniciado"
            })
        
        preference_id = preference.get("preference_id")
        
        # 3. 🔥 BUSCAR PAGOS ASOCIADOS A ESA PREFERENCIA EN MERCADO PAGO
        try:
            # Buscar pagos por external_reference
            filters = {
                "external_reference": str(cuenta_id)
            }
            
            search_result = sdk.payment().search(filters=filters)

            if search_result["status"] == 200:
                results = search_result["response"].get("results", [])
                
                if results:
                    # Tomar el pago más reciente
                    pago = results[0]
                    status = pago.get("status")
                    payment_id = pago.get("id")

                    if status == "approved":
                        # 🔥 PAGO APROBADO - CERRAR LA CUENTA
                        metadata = pago.get("metadata", {})
                        propina = float(metadata.get("propina", preference.get("propina", 0)))
                        porcentaje_propina = float(metadata.get("porcentaje_propina", preference.get("porcentaje_propina", 0)))
                        
                        total = float(comanda.get("total", 0))
                        total_final = total + propina
                        mesa_numero = comanda.get("mesa_numero")
                        
                        # 🔥 USAR HORA LOCAL (NO UTC)
                        fecha_actual = datetime.now()

                        # Cerrar comanda
                        db.comandas.update_one(
                            {"_id": cuenta_oid},
                            {
                                "$set": {
                                    "estado": "pagada",
                                    "metodo_pago": "mercadopago",
                                    "fecha_cierre": fecha_actual,
                                    "propina": propina,
                                    "porcentaje_propina": porcentaje_propina,
                                    "total_final": total_final,
                                    "payment_id": payment_id
                                }
                            }
                        )
                        
                        # Liberar mesa
                        db.mesas.update_one(
                            {"numero": mesa_numero},
                            {
                                "$set": {
                                    "estado": "disponible",
                                    "cuenta_activa_id": None,
                                    "num_comensales": 0,
                                    "ultima_actualizacion": fecha_actual
                                }
                            }
                        )
                        
                        # Registrar propina
                        if propina > 0 and comanda.get("mesero_id"):
                            db.propinas.insert_one({
                                "mesero_id": comanda.get("mesero_id"),
                                "comanda_id": cuenta_oid,
                                "mesa_numero": mesa_numero,
                                "monto": propina,
                                "porcentaje": porcentaje_propina,
                                "fecha": fecha_actual,
                                "metodo_pago": "mercadopago"
                            })
                        
                        # Actualizar preferencia
                        db.payment_preferences.update_one(
                            {"preference_id": preference_id},
                            {"$set": {"status": "approved"}}
                        )

                        Ticket.create(
                            comanda=comanda,
                            metodo_pago="mercadopago",
                            propina=propina,
                            porcentaje_propina=porcentaje_propina,
                            total_final=total_final,
                            fecha_cierre=fecha_actual,
                            payment_id=payment_id,
                        )

                        print(f"✅ Cuenta {cuenta_id} cerrada por pago aprobado")

                        return jsonify({
                            "success": True,
                            "status": "approved",
                            "total": total_final,
                            "propina": propina,
                            "payment_id": payment_id
                        })
                    
                    elif status == "rejected":
                        return jsonify({
                            "success": True,
                            "status": "rejected",
                            "message": "Pago rechazado"
                        })
                    
                    elif status in ["in_process", "pending"]:
                        return jsonify({
                            "success": True,
                            "status": "pending",
                            "message": "Pago en proceso"
                        })
            
            # Si no se encontró pago, sigue pendiente
            return jsonify({
                "success": True,
                "status": "pending",
                "message": "Esperando confirmación del pago"
            })
                
        except Exception as e:
            print(f"❌ Error al buscar pago en MP: {e}")
            return jsonify({
                "success": True,
                "status": "pending",
                "error": str(e)
            })

    @staticmethod
    def procesar_pago_exitoso():
        """Procesa un pago exitoso (si usas túnel con back_urls)"""
        cuenta_id = request.args.get("cuenta_id")
        payment_id = request.args.get("payment_id")
        
        # Redirigir al dashboard con mensaje
        return redirect(url_for("routes.dashboard_mesero") + f"?pago=exitoso&cuenta_id={cuenta_id}")

    @staticmethod
    def procesar_pago_fallido():
        """Procesa un pago fallido"""
        return redirect(url_for("routes.dashboard_mesero") + "?pago=fallido")

    @staticmethod
    def procesar_pago_pendiente():
        """Procesa un pago pendiente"""
        return redirect(url_for("routes.dashboard_mesero") + "?pago=pendiente")

    @staticmethod
    def webhook():
        """Recibe notificaciones de Mercado Pago (IPN/Webhook)."""
        data = request.get_json(silent=True) or {}

        topic   = data.get("topic") or data.get("type", "")
        mp_id   = data.get("id") or data.get("data", {}).get("id")

        if topic in ("payment", "merchant_order") and mp_id:
            try:
                payment_info = sdk.payment().get(mp_id)
                if payment_info.get("status") == 200:
                    p        = payment_info["response"]
                    estado   = p.get("status")
                    ext_ref  = p.get("external_reference", "")
                    pago_id_mp = str(p.get("id", ""))

                    if ext_ref.startswith("MOVIL_"):
                        # Pago móvil
                        from models.pago_movil_model import PagoMovil
                        pago_id = ext_ref[len("MOVIL_"):]
                        pago_doc = PagoMovil.find_by_id(pago_id)
                        if pago_doc and estado == "approved":
                            PagoMovil.set_aprobado(pago_id, pago_id_mp)
                            # Notificar al cliente
                            try:
                                from extensions import socketio
                                socketio.emit(
                                    "pago_aprobado",
                                    {"pedido_id": pago_doc.get("pedido_id"),
                                     "pago_id": pago_id,
                                     "total_final": pago_doc.get("total_final")},
                                    room=f"cliente_{pago_doc.get('cliente_id')}",
                                    namespace="/",
                                )
                                socketio.emit(
                                    "pago_aprobado_movil",
                                    {"pedido_id": pago_doc.get("pedido_id"),
                                     "pago_id": pago_id},
                                    room="meseros", namespace="/",
                                )
                            except Exception:
                                pass
                        elif pago_doc and estado in ("rejected", "cancelled"):
                            PagoMovil.set_rechazado(pago_id)
            except Exception as e:
                print(f"⚠️ Error procesando webhook MP: {e}")

        return jsonify({"success": True}), 200