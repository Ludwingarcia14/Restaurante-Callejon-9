"""
Controlador de Ventas - Gestión de ventas, cuentas y corte de caja
"""
from flask import render_template, session, redirect, url_for, request, jsonify
from models.venta_model import Venta, Cuenta, CorteCaja
from models.mesa_model import Mesa
from models.menu_model import Platillo
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class VentasController:
    # ============================================
    # VISTAS PRINCIPALES
    # ============================================
    
    @staticmethod
    def dashboard():
        """Dashboard de ventas"""
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))
        
        # Obtener estadísticas del día
        stats = Venta.get_estadisticas_hoy()
        
        # Obtener ventas recientes
        ventas_recientes = Venta.find_hoy()[:10]
        
        # Obtener cuentas abiertas
        cuentas_abiertas = Cuenta.find_abiertas()
        
        return render_template("admin/ventas/dashboard.html", 
                             stats=stats,
                             ventas_recientes=ventas_recientes,
                             cuentas_abiertas=cuentas_abiertas)
    
    @staticmethod
    def nueva_venta():
        """Formulario para nueva venta"""
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))
        
        # Obtener mesas disponibles
        mesas = Mesa.find_all()
        
        # Obtener menú disponible
        menu = Platillo.find_disponibles()
        
        return render_template("admin/ventas/nueva_venta.html",
                             mesas=mesas,
                             menu=menu)
    
    @staticmethod
    def cuentas():
        """Lista de cuentas abiertas"""
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))
        
        cuentas = Cuenta.find_abiertas()
        
        return render_template("admin/ventas/cuentas.html",
                             cuentas=cuentas)
    
    @staticmethod
    def cerrar_cuenta(cuenta_id):
        """Formulario para cerrar una cuenta"""
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))
        
        cuenta = Cuenta.find_by_id(cuenta_id)
        if not cuenta:
            return redirect(url_for("routes.ventas_cuentas"))
        
        # Obtener la venta asociada
        venta = Venta.find_by_mesa(cuenta.get("mesa_id"))
        
        return render_template("admin/ventas/cerrar_cuenta.html",
                             cuenta=cuenta,
                             venta=venta)
    
    @staticmethod
    def corte_caja():
        """Vista de corte de caja"""
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))
        
        # Obtener ventas de hoy
        ventas_hoy = Venta.find_hoy()
        
        # Calcular estadísticas
        stats = {
            "total_ventas": sum(v.get("total", 0) for v in ventas_hoy),
            "num_transacciones": len(ventas_hoy),
            "efectivo": 0,
            "tarjeta": 0,
            "transferencia": 0,
            "propinas": sum(v.get("propina", 0) for v in ventas_hoy)
        }
        
        # Agrupar por método de pago
        for venta in ventas_hoy:
            metodo = venta.get("metodo_pago", "efectivo")
            if metodo == "efectivo":
                stats["efectivo"] += venta.get("total", 0)
            elif metodo == "tarjeta":
                stats["tarjeta"] += venta.get("total", 0)
            elif metodo == "transferencia":
                stats["transferencia"] += venta.get("total", 0)
        
        # Obtener últimos cortes
        ultimos_cortes = CorteCaja.find_all()[:5]
        
        return render_template("admin/ventas/corte_caja.html",
                             stats=stats,
                             ventas=ventas_hoy,
                             ultimos_cortes=ultimos_cortes)
    
    # ============================================
    # API: VENTAS
    # ============================================
    
    @staticmethod
    def api_crear_venta():
        """API: Crea una nueva venta"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            data = request.get_json()
            
            # Crear la cuenta
            cuenta_data = {
                "mesa_id": data.get("mesa_id"),
                "mesa_nombre": data.get("mesa_nombre"),
                "mesero_id": session.get("usuario_id"),
                "mesero_nombre": session.get("usuario_nombre", ""),
                "cliente_nombre": data.get("cliente_nombre", ""),
                "num_personas": data.get("num_personas", 1)
            }
            cuenta_id = Cuenta.create(cuenta_data)
            
            # Crear la venta
            venta_data = {
                "cuenta_id": cuenta_id,
                "mesa_id": data.get("mesa_id"),
                "mesa_nombre": data.get("mesa_nombre"),
                "mesero_id": session.get("usuario_id"),
                "mesero_nombre": session.get("usuario_nombre", ""),
                "cliente_nombre": data.get("cliente_nombre", ""),
                "items": data.get("items", []),
                "subtotal": data.get("subtotal", 0),
                "impuesto": data.get("impuesto", 0),
                "descuento": data.get("descuento", 0),
                "propina": data.get("propina", 0),
                "total": data.get("total", 0),
                "metodo_pago": "efectivo",
                "estado": "pendiente"
            }
            venta_id = Venta.create(venta_data)
            
            return jsonify({
                "success": True,
                "message": "Venta creada correctamente",
                "venta_id": venta_id,
                "cuenta_id": cuenta_id
            })
        except Exception as e:
            logger.error(f"Error en api_crear_venta: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_actualizar_venta(venta_id):
        """API: Actualiza una venta"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            data = request.get_json()
            success = Venta.update(venta_id, data)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Venta actualizada correctamente"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "No se pudo actualizar la venta"
                }), 400
        except Exception as e:
            logger.error(f"Error en api_get_cortes: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_completar_venta(venta_id):
        """API: Completa una venta"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            metodo_pago = request.get_json().get("metodo_pago", "efectivo") if request.get_json() else "efectivo"
            success = Venta.completar(venta_id, metodo_pago)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Venta completada correctamente"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "No se pudo completar la venta"
                }), 400
        except Exception as e:
            logger.error(f"Error en api_completar_venta: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_cancelar_venta(venta_id):
        """API: Cancela una venta"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            data = request.get_json() or {}
            motivo = data.get("motivo", "")
            success = Venta.cancelar(venta_id, motivo)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Venta cancelada correctamente"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "No se pudo cancelar la venta"
                }), 400
        except Exception as e:
            logger.error(f"Error en api_cancelar_venta: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_eliminar_venta(venta_id):
        """API: Elimina una venta"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            success = Venta.delete(venta_id)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Venta eliminada correctamente"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "No se pudo eliminar la venta"
                }), 400
        except Exception as e:
            logger.error(f"Error en api_eliminar_venta: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_get_venta(venta_id):
        """API: Obtiene una venta"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            venta = Venta.find_by_id(venta_id)
            
            if venta:
                return jsonify({
                    "success": True,
                    "venta": venta
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "Venta no encontrada"
                }), 404
        except Exception as e:
            logger.error(f"Error en api_get_venta: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_get_ventas():
        """API: Obtiene ventas con filtros"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            estado = request.args.get("estado")
            fecha_inicio = request.args.get("fecha_inicio")
            fecha_fin = request.args.get("fecha_fin")
            
            filtro = {}
            if estado:
                filtro["estado"] = estado
            if fecha_inicio and fecha_fin:
                ventas = Venta.find_by_fecha(
                    datetime.fromisoformat(fecha_inicio),
                    datetime.fromisoformat(fecha_fin)
                )
            else:
                ventas = Venta.find_all(filtro)
            
            return jsonify({
                "success": True,
                "ventas": ventas
            })
        except Exception as e:
            logger.error(f"Error en api_get_ventas: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_get_estadisticas():
        """API: Obtiene estadísticas de ventas"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            stats = Venta.get_estadisticas_hoy()
            
            return jsonify({
                "success": True,
                "stats": stats
            })
        except Exception as e:
            logger.error(f"Error en api_get_estadisticas: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    # ============================================
    # API: CUENTAS
    # ============================================
    
    @staticmethod
    def api_cerrar_cuenta(cuenta_id):
        """API: Cierra una cuenta"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            data = request.get_json()
            
            datos_pago = {
                "metodo_pago": data.get("metodo_pago", "efectivo"),
                "total": data.get("total", 0),
                "propina": data.get("propina", 0)
            }
            
            success = Cuenta.cerrar(cuenta_id, datos_pago)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Cuenta cerrada correctamente"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "No se pudo cerrar la cuenta"
                }), 400
        except Exception as e:
            logger.error(f"Error en api_cerrar_cuenta: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_get_cuentas():
        """API: Obtiene cuentas abiertas"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            cuentas = Cuenta.find_abiertas()
            
            return jsonify({
                "success": True,
                "cuentas": cuentas
            })
        except Exception as e:
            logger.error(f"Error en api_get_cuentas: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    # ============================================
    # API: CORTE DE CAJA
    # ============================================
    
    @staticmethod
    def api_generar_corte():
        """API: Genera un corte de caja"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            # Obtener ventas de hoy
            ventas_hoy = Venta.find_hoy()
            
            # Calcular totales
            total_ventas = sum(v.get("total", 0) for v in ventas_hoy)
            total_efectivo = sum(v.get("total", 0) for v in ventas_hoy if v.get("metodo_pago") == "efectivo")
            total_tarjeta = sum(v.get("total", 0) for v in ventas_hoy if v.get("metodo_pago") == "tarjeta")
            total_transferencia = sum(v.get("total", 0) for v in ventas_hoy if v.get("metodo_pago") == "transferencia")
            total_propinas = sum(v.get("propina", 0) for v in ventas_hoy)
            
            # Crear el corte
            data = {
                "usuario_id": session.get("usuario_id"),
                "usuario_nombre": session.get("usuario_nombre", ""),
                "fecha_inicio": datetime.now().replace(hour=0, minute=0, second=0),
                "fecha_fin": datetime.utcnow(),
                "ventas": [str(v.get("_id")) for v in ventas_hoy],
                "total_ventas": total_ventas,
                "total_efectivo": total_efectivo,
                "total_tarjeta": total_tarjeta,
                "total_transferencia": total_transferencia,
                "total_propinas": total_propinas,
                "num_transacciones": len(ventas_hoy),
                "notas": request.get_json().get("notas", "") if request.get_json() else ""
            }
            
            corte_id = CorteCaja.create(data)
            
            return jsonify({
                "success": True,
                "message": "Corte de caja generado correctamente",
                "corte_id": corte_id
            })
        except Exception as e:
            logger.error(f"Error en api_generar_corte: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_get_cortes():
        """API: Obtiene cortes de caja"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            cortes = CorteCaja.find_all()
            
            return jsonify({
                "success": True,
                "cortes": cortes
            })
        except Exception as e:
            logger.error(f"Error en api_crear_venta: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
