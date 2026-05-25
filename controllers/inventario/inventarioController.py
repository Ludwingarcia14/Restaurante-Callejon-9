"""
Dashboard Controller - Inventario
Rol 4: Encargado de Inventario/Almacén
"""
from flask import request, session, redirect, url_for, render_template, jsonify
from models.inventario_model import (
    Insumo, MovimientoInventario, Proveedor, AlertaStock,
    TipoMovimiento, UnidadMedida, CategoriaInsumo
)
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from controllers.notificaciones.notificacion_controller import NotificacionSistemaController
import logging
import json

logging.basicConfig(level=logging.INFO)


class InventarioController:

    # ==========================================
    # DASHBOARD
    # ==========================================
    @staticmethod
    def dashboard():
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "3", "4"]:
            return redirect(url_for("routes.login"))

        if str(session["usuario_rol"]) == "3":
            return redirect(url_for("routes.inventario_reportes"))

        try:
            total_insumos = len(Insumo.obtener_todos())
            insumos_criticos = Insumo.obtener_stock_critico()
            alertas_activas = AlertaStock.obtener_alertas_activas()

            hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            movimientos_hoy = MovimientoInventario.obtener_historial(
                {"fecha": {"$gte": hoy_inicio}},
                limit=10
            )

            insumos = Insumo.obtener_todos()
            valor_total = sum(
                i.get("stock_actual", 0) * i.get("costo_unitario", 0)
                for i in insumos
            )

            stats = {
                "total_insumos": total_insumos,
                "stock_critico": len(insumos_criticos),
                "alertas_activas": len(alertas_activas),
                "valor_inventario": valor_total,
                "movimientos_hoy": len(movimientos_hoy)
            }

            return render_template(
                "inventario/dashboard.html",
                usuario=session.get("usuario_nombre"),
                stats=stats,
                alertas=alertas_activas[:5],
                movimientos_recientes=movimientos_hoy[:5]
            )

        except Exception as e:
            logging.error(f"Error en dashboard de inventario: {str(e)}")
            return "Error interno del servidor", 500

    # ==========================================
    # INSUMOS
    # ==========================================
    @staticmethod
    def lista_insumos():
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4"]:
            return redirect(url_for("routes.login"))

        try:
            categoria = request.args.get("categoria")
            filtros = {"activo": True}

            if categoria and categoria != "todas":
                filtros["categoria"] = categoria

            insumos = Insumo.obtener_todos(filtros)

            for insumo in insumos:
                stock = insumo.get("stock_actual", 0)
                minimo = insumo.get("stock_minimo", 0)

                if stock == 0:
                    insumo["estado_stock"] = "agotado"
                elif stock <= minimo:
                    insumo["estado_stock"] = "critico"
                elif stock <= minimo * 1.5:
                    insumo["estado_stock"] = "bajo"
                else:
                    insumo["estado_stock"] = "normal"

            categorias = [cat.value for cat in CategoriaInsumo]

            return render_template(
                "inventario/insumos/lista.html",
                insumos=insumos,
                categorias=categorias,
                categoria_seleccionada=categoria
            )

        except Exception as e:
            logging.error(f"Error al listar insumos: {str(e)}")
            return render_template("inventario/insumos/lista.html", error="Error interno del servidor")
    
    @staticmethod
    def crear_insumo():
        """Formulario y procesamiento de creación de insumo"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4"]:
            return redirect(url_for("routes.login"))
        
        if request.method == "POST":
            try:
                data = request.get_json()
                
                # Validaciones
                required = ["nombre", "categoria", "unidad_medida", "stock_minimo"]
                for field in required:
                    if not data.get(field):
                        return jsonify({
                            "success": False,
                            "message": f"El campo '{field}' es obligatorio"
                        }), 400
                
                # Crear insumo
                insumo_id = Insumo.crear_insumo(data)
                
                return jsonify({
                    "success": True,
                    "message": "Insumo creado exitosamente",
                    "insumo_id": str(insumo_id)
                })
                
            except Exception as e:
                logging.error(f"Error al crear insumo: {e}")
                return jsonify({
                    "success": False,
                    "message": "Error al crear insumo"
                }), 500
        
        # GET - Mostrar formulario
        proveedores = Proveedor.obtener_todos()
        categorias = [cat.value for cat in CategoriaInsumo]
        unidades = [u.value for u in UnidadMedida]
        
        return render_template(
            "inventario/insumos/crear.html",
            proveedores=proveedores,
            categorias=categorias,
            unidades=unidades
        )
    
    # ==========================================
    # MOVIMIENTOS
    # ==========================================
    @staticmethod
    def registrar_entrada():
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4"]:
            return redirect(url_for("routes.login"))

        if request.method == "POST":
            try:
                data = request.get_json()

                movimiento_data = {
                    "tipo": TipoMovimiento.ENTRADA,
                    "insumo_id": data["insumo_id"],
                    "cantidad": float(data["cantidad"]),
                    "costo_unitario": float(data["costo_unitario"]),
                    "usuario_id": session["usuario_id"]
                }

                resultado = MovimientoInventario.registrar_movimiento(movimiento_data)

                if resultado["success"]:
                    AlertaStock.generar_alertas_automaticas()

                    # Notificación
                    NotificacionSistemaController.notificar_movimiento_inventario(
                        usuario_id=session.get("usuario_id"),
                        tipo_movimiento="entrada",
                        nombre_insumo=data.get("nombre_insumo", "Insumo"),
                        cantidad=data["cantidad"]
                    )

                    return jsonify({"success": True})

                return jsonify({"success": False}), 400

            except Exception as e:
                logging.error(e)
                return jsonify({"success": False}), 500

        insumos = Insumo.obtener_todos()
        proveedores = Proveedor.obtener_todos()

        return render_template(
            "inventario/movimientos/entrada.html",
            insumos=insumos,
            proveedores=proveedores
        )

    @staticmethod
    def historial_movimientos():
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4"]:
            return redirect(url_for("routes.login"))
        
        try:
            # Filtros
            insumo_id = request.args.get("insumo_id")
            tipo = request.args.get("tipo")
            fecha_desde = request.args.get("fecha_desde")
            fecha_hasta = request.args.get("fecha_hasta")
            
            filtros = {}
            
            if insumo_id:
                filtros["insumo_id"] = ObjectId(insumo_id)
            if tipo and tipo != "todos":
                filtros["tipo"] = tipo
            if fecha_desde:
                filtros["fecha_desde"] = datetime.strptime(fecha_desde, "%Y-%m-%d")
            if fecha_hasta:
                filtros["fecha_hasta"] = datetime.strptime(fecha_hasta, "%Y-%m-%d")
            
            movimientos = MovimientoInventario.obtener_historial(filtros, limit=200)
            insumos = Insumo.obtener_todos()
            tipos_movimiento = [t.value for t in TipoMovimiento]
            
            return render_template(
                "inventario/movimientos/historial.html",
                movimientos=movimientos,
                insumos=insumos,
                tipos_movimiento=tipos_movimiento
            )
            
        except Exception as e:
            logging.error(f"Error al obtener historial: {str(e)}")
            return render_template("inventario/movimientos/historial.html", error="Error interno del servidor")
    
    # ==========================================
    # ALERTAS
    # ==========================================
    @staticmethod
    def alertas_stock():
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4"]:
            return redirect(url_for("routes.login"))
        
        try:
            alertas = AlertaStock.obtener_alertas_activas()
            
            return render_template(
                "inventario/alertas.html",
                alertas=alertas
            )
            
        except Exception as e:
            logging.error(f"Error al obtener alertas: {str(e)}")
            return render_template("inventario/alertas.html", error="Error interno del servidor")
    
    @staticmethod
    def resolver_alerta():
        """Marca una alerta como resuelta"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4"]:
            return jsonify({"success": False, "message": "No autorizado"}), 403
        
        try:
            data = request.get_json()
            alerta_id = data.get("alerta_id")
            
            if not alerta_id:
                return jsonify({
                    "success": False,
                    "message": "ID de alerta requerido"
                }), 400
            
            AlertaStock.resolver_alerta(alerta_id, session["usuario_id"])
            
            return jsonify({
                "success": True,
                "message": "Alerta resuelta"
            })
            
        except Exception as e:
            logging.error(f"Error al resolver alerta: {e}")
            return jsonify({
                "success": False,
                "message": "Error al resolver alerta"
            }), 500
    
    # ==========================================
    # PROVEEDORES
    # ==========================================
    @staticmethod
    def lista_proveedores():
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4"]:
            return redirect(url_for("routes.login"))
        
        try:
            proveedores = Proveedor.obtener_todos()
            
            return render_template(
                "inventario/proveedores/lista.html",
                proveedores=proveedores
            )
            
        except Exception as e:
            logging.error(f"Error al listar proveedores: {str(e)}")
            return render_template("inventario/proveedores/lista.html", error="Error interno del servidor")
    
    @staticmethod
    def crear_proveedor():
        """Crea un nuevo proveedor"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4"]:
            return redirect(url_for("routes.login"))
        
        if request.method == "POST":
            try:
                data = request.get_json()
                
                if not data.get("nombre"):
                    return jsonify({
                        "success": False,
                        "message": "El nombre es obligatorio"
                    }), 400
                
                proveedor_id = Proveedor.crear_proveedor(data)
                
                return jsonify({
                    "success": True,
                    "message": "Proveedor creado exitosamente",
                    "proveedor_id": str(proveedor_id)
                })
                
            except Exception as e:
                logging.error(f"Error al crear proveedor: {e}")
                return jsonify({
                    "success": False,
                    "message": "Error al crear proveedor"
                }), 500
        
        # GET
        return render_template("inventario/proveedores/crear.html")
    
    # ==========================================
    # REPORTES
    # ==========================================
    @staticmethod
    def reportes():
        """Dashboard de reportes de inventario"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4", "3"]:
            return redirect(url_for("routes.login"))

        try:
            insumos = Insumo.obtener_todos({"activo": True})
            criticos = Insumo.obtener_stock_critico()

            total_insumos = len(insumos)
            total_criticos = len(criticos)
            total_normales = total_insumos - total_criticos
            valor_total = round(sum(
                float(i.get("stock_actual", 0)) * float(i.get("costo_unitario", 0))
                for i in insumos
            ), 2)

            chart_estado = json.dumps({
                "labels": ["Normal", "Crítico"],
                "data": [total_normales, total_criticos],
                "colors": ["#22c55e", "#ef4444"]
            })

            top5 = sorted(
                insumos,
                key=lambda x: float(x.get("stock_actual", 0)) * float(x.get("costo_unitario", 0)),
                reverse=True
            )[:5]
            chart_top_valor = json.dumps({
                "labels": [i.get("nombre", "") for i in top5],
                "data": [
                    round(float(i.get("stock_actual", 0)) * float(i.get("costo_unitario", 0)), 2)
                    for i in top5
                ]
            })

            return render_template(
                "reports/inventario.html",
                total_insumos=total_insumos,
                total_criticos=total_criticos,
                total_normales=total_normales,
                valor_total=valor_total,
                chart_estado=chart_estado,
                chart_top_valor=chart_top_valor
            )

        except Exception as e:
            logging.error(f"Error en reportes inventario: {e}")
            return render_template(
                "reports/inventario.html",
                total_insumos=0, total_criticos=0,
                total_normales=0, valor_total=0,
                chart_estado=json.dumps({"labels": [], "data": [], "colors": []}),
                chart_top_valor=json.dumps({"labels": [], "data": []})
            )