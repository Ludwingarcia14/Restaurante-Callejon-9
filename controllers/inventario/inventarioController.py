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
from datetime import datetime

logging.basicConfig(level=logging.INFO)


class InventarioController:
    """Controlador principal para el módulo de inventario"""
    
    # ==========================================
    # DASHBOARD
    # ==========================================
    
    @staticmethod
    def dashboard():
        """Dashboard principal del encargado de inventario"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "4":
            return redirect(url_for("routes.login"))
        
        try:
            # Obtener estadísticas generales
            total_insumos = len(Insumo.obtener_todos())
            insumos_criticos = Insumo.obtener_stock_critico()
            alertas_activas = AlertaStock.obtener_alertas_activas()
            
            # Movimientos del día
            hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            movimientos_hoy = MovimientoInventario.obtener_historial(
                {"fecha": {"$gte": hoy_inicio}},
                limit=10
            )
            
            # Calcular valor total del inventario (aproximado)
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
                alertas=alertas_activas[:5],  # Solo las 5 más críticas
                movimientos_recientes=movimientos_hoy[:5]
            )
            
        except Exception as e:
            logging.error(f"Error en dashboard de inventario: {e}")
            return str(e), 500

    # ==========================================
    # GESTIÓN DE INSUMOS
    # ==========================================
    
    @staticmethod
    def lista_insumos():
        """Lista todos los insumos"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4"]:
            return redirect(url_for("routes.login"))
        
        try:
            categoria = request.args.get("categoria")
            filtros: dict = {"activo": True}
            
            if categoria and categoria != "todas":
                filtros["categoria"] = categoria
            
            insumos = Insumo.obtener_todos(filtros)
            
            # Enriquecer con estado de stock
            for insumo in insumos:
                stock_actual = insumo.get("stock_actual", 0)
                stock_minimo = insumo.get("stock_minimo", 0)
                
                if stock_actual == 0:
                    insumo["estado_stock"] = "agotado"
                elif stock_actual <= stock_minimo:
                    insumo["estado_stock"] = "critico"
                elif stock_actual <= stock_minimo * 1.5:
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
            logging.error(f"Error al listar insumos: {e}")
            return render_template("inventario/insumos/lista.html", error=str(e))
    
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
    # MOVIMIENTOS DE INVENTARIO
    # ==========================================
    
    @staticmethod
    def registrar_entrada():
        """Registra una entrada de inventario (compra, devolución)"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4"]:
            return redirect(url_for("routes.login"))
        
        if request.method == "POST":
            try:
                data = request.get_json()
                
                # Validaciones
                required = ["insumo_id", "cantidad", "costo_unitario"]
                for field in required:
                    if not data.get(field):
                        return jsonify({
                            "success": False,
                            "message": f"El campo '{field}' es obligatorio"
                        }), 400
                
                # Preparar datos del movimiento
                movimiento_data = {
                    "tipo": TipoMovimiento.ENTRADA,
                    "insumo_id": data["insumo_id"],
                    "cantidad": float(data["cantidad"]),
                    "costo_unitario": float(data["costo_unitario"]),
                    "usuario_id": session["usuario_id"],
                    "proveedor_id": data.get("proveedor_id"),
                    "referencia": data.get("referencia", ""),
                    "motivo": data.get("motivo", "Compra")
                }
                
                # Registrar movimiento
                resultado = MovimientoInventario.registrar_movimiento(movimiento_data)
                
                if resultado["success"]:
                    # Generar alertas automáticas
                    AlertaStock.generar_alertas_automaticas()
                    
                    return jsonify({
                        "success": True,
                        "message": "Entrada registrada exitosamente",
                        "stock_nuevo": resultado["stock_nuevo"]
                    })
                else:
                    return jsonify({
                        "success": False,
                        "message": resultado.get("error", "Error desconocido")
                    }), 400
                    
            except Exception as e:
                logging.error(f"Error al registrar entrada: {e}")
                return jsonify({
                    "success": False,
                    "message": "Error al registrar entrada"
                }), 500
        
        # GET - Mostrar formulario
        insumos = Insumo.obtener_todos()
        proveedores = Proveedor.obtener_todos()
        
        return render_template(
            "inventario/movimientos/entrada.html",
            insumos=insumos,
            proveedores=proveedores
        )
    
    @staticmethod
    def registrar_salida():
        """Registra una salida manual de inventario"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4"]:
            return redirect(url_for("routes.login"))
        
        if request.method == "POST":
            try:
                data = request.get_json()
                
                movimiento_data = {
                    "tipo": TipoMovimiento.SALIDA,
                    "insumo_id": data["insumo_id"],
                    "cantidad": float(data["cantidad"]),
                    "usuario_id": session["usuario_id"],
                    "motivo": data.get("motivo", "Salida manual")
                }
                
                resultado = MovimientoInventario.registrar_movimiento(movimiento_data)
                
                if resultado["success"]:
                    AlertaStock.generar_alertas_automaticas()
                    
                    return jsonify({
                        "success": True,
                        "message": "Salida registrada exitosamente",
                        "stock_nuevo": resultado["stock_nuevo"]
                    })
                else:
                    return jsonify({
                        "success": False,
                        "message": resultado.get("error")
                    }), 400
                    
            except Exception as e:
                logging.error(f"Error al registrar salida: {e}")
                return jsonify({
                    "success": False,
                    "message": "Error al registrar salida"
                }), 500
        
        # GET
        insumos = Insumo.obtener_todos()
        return render_template("inventario/movimientos/salida.html", insumos=insumos)
    
    @staticmethod
    def registrar_merma():
        """Registra una merma (pérdida, caducidad, daño)"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4"]:
            return redirect(url_for("routes.login"))
        
        if request.method == "POST":
            try:
                data = request.get_json()
                
                movimiento_data = {
                    "tipo": TipoMovimiento.MERMA,
                    "insumo_id": data["insumo_id"],
                    "cantidad": float(data["cantidad"]),
                    "usuario_id": session["usuario_id"],
                    "motivo": data.get("motivo", "Merma")
                }
                
                resultado = MovimientoInventario.registrar_movimiento(movimiento_data)
                
                if resultado["success"]:
                    AlertaStock.generar_alertas_automaticas()
                    
                    return jsonify({
                        "success": True,
                        "message": "Merma registrada exitosamente",
                        "stock_nuevo": resultado["stock_nuevo"]
                    })
                else:
                    return jsonify({
                        "success": False,
                        "message": resultado.get("error")
                    }), 400
                    
            except Exception as e:
                logging.error(f"Error al registrar merma: {e}")
                return jsonify({
                    "success": False,
                    "message": "Error al registrar merma"
                }), 500
        
        # GET
        insumos = Insumo.obtener_todos()
        return render_template("inventario/movimientos/merma.html", insumos=insumos)
    
    @staticmethod
    def historial_movimientos():
        """Muestra el historial completo de movimientos"""
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
            logging.error(f"Error al obtener historial: {e}")
            return render_template("inventario/movimientos/historial.html", error=str(e))
    
    # ==========================================
    # ALERTAS
    # ==========================================
    
    @staticmethod
    def alertas_stock():
        """Muestra las alertas de stock crítico"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4"]:
            return redirect(url_for("routes.login"))
        
        try:
            alertas = AlertaStock.obtener_alertas_activas()
            
            return render_template(
                "inventario/alertas.html",
                alertas=alertas
            )
            
        except Exception as e:
            logging.error(f"Error al obtener alertas: {e}")
            return render_template("inventario/alertas.html", error=str(e))
    
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
        """Lista todos los proveedores"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4"]:
            return redirect(url_for("routes.login"))
        
        try:
            proveedores = Proveedor.obtener_todos()
            
            return render_template(
                "inventario/proveedores/lista.html",
                proveedores=proveedores
            )
            
        except Exception as e:
            logging.error(f"Error al listar proveedores: {e}")
            return render_template("inventario/proveedores/lista.html", error=str(e))
    
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
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4"]:
            return redirect(url_for("routes.login"))
        
        return render_template("inventario/reportes/index.html")
    
    # En controllers/inventario/inventarioController.py

    
    @staticmethod
    def registrar_entrada():
        if request.method == "POST":
            nombre_insumo = request.form.get("nombre_insumo")
            cantidad = int(request.form.get("cantidad"))
            
            # ... registrar entrada ...
            
            # ✨ NOTIFICAR MOVIMIENTO
            NotificacionSistemaController.notificar_movimiento_inventario(
                usuario_id=session.get("usuario_id"),
                tipo_movimiento="entrada",
                nombre_insumo=nombre_insumo,
                cantidad=cantidad
            )
            
            return redirect(...)