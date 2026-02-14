import os
import mercadopago
from flask import jsonify, request, redirect, url_for, session
from config.db import db
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Inicializa SDK
sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
NGROK_URL = os.getenv("NGROK_URL", "http://localhost:5000")

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

        print("📦 Creando preferencia con datos:", preference_data)

        result = sdk.preference().create(preference_data)

        print("📦 RESULTADO MP:", result)

        if result["status"] not in [200, 201]:
            return jsonify({
                "success": False,
                "error": result.get("response", {}).get("message", "Error al crear preferencia")
            }), 400

        preference = result["response"]
        
        # 🔥 USA SANDBOX EN DESARROLLO
        init_point = preference.get("sandbox_init_point") or preference.get("init_point")
        preference_id = preference.get("id")

        print(f"✅ Init Point generado: {init_point}")
        print(f"✅ Preference ID: {preference_id}")

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
            
            print(f"🔍 Búsqueda de pagos para cuenta {cuenta_id}:", search_result)
            
            if search_result["status"] == 200:
                results = search_result["response"].get("results", [])
                
                if results:
                    # Tomar el pago más reciente
                    pago = results[0]
                    status = pago.get("status")
                    payment_id = pago.get("id")
                    
                    print(f"💳 Pago encontrado - ID: {payment_id}, Status: {status}")
                    
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
                        
                        print(f"\n{'='*60}")
                        print(f"💳 CERRANDO CUENTA POR PAGO APROBADO")
                        print(f"{'='*60}")
                        print(f"Cuenta ID: {cuenta_id}")
                        print(f"Payment ID: {payment_id}")
                        print(f"Total: ${total_final:.2f}")
                        print(f"Propina: ${propina:.2f}")
                        print(f"Fecha cierre: {fecha_actual}")
                        print(f"{'='*60}\n")
                        
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
        """Recibe notificaciones de Mercado Pago (IPN) - Solo funciona con túnel"""
        data = request.get_json()
        print(f"🔔 WEBHOOK RECIBIDO: {data}")
        
        # Siempre responder 200 OK a Mercado Pago
        return jsonify({"success": True}), 200