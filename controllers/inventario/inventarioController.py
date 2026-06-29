"""
Dashboard Controller - Inventario
Rol 4: Encargado de Inventario/Almacén
"""
from flask import request, session, redirect, url_for, render_template, jsonify
from models.inventario_model import (
    Insumo, MovimientoInventario, Proveedor, AlertaStock,
    TipoMovimiento, UnidadMedida, CategoriaInsumo
)
from services.inventario.inventario_service import calcular_valor_inventario
from bson.objectid import ObjectId
from collections import Counter
from datetime import datetime, timedelta
from collections import defaultdict
from controllers.notificaciones.notificacion_controller import NotificacionSistemaController
import logging
import json

logging.basicConfig(level=logging.INFO)


def _build_chart_data(insumos, criticos):
    """Genera los datos comunes de gráficas para reportes e inventario."""
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

    categorias = {}
    for i in insumos:
        cat = i.get("categoria", "Sin categoría")
        categorias[cat] = categorias.get(cat, 0) + 1
    chart_categorias = json.dumps({
        "labels": list(categorias.keys()),
        "data": list(categorias.values())
    })

    # Historial diario del último mes por tipo
    hace_un_mes = datetime.now() - timedelta(days=30)
    movimientos = MovimientoInventario.obtener_historial(
        {"fecha": {"$gte": hace_un_mes}}, limit=1000
    )
    tipos = ["entrada", "salida", "merma", "ajuste"]
    por_dia = defaultdict(lambda: {t: 0 for t in tipos})
    for m in movimientos:
        fecha = m.get("fecha")
        tipo = m.get("tipo", "")
        if fecha and tipo in tipos:
            dia = fecha.strftime("%d/%m")
            por_dia[dia][tipo] += 1
    dias = sorted(por_dia.keys(),
                  key=lambda d: datetime.strptime(d + f"/{datetime.now().year}", "%d/%m/%Y"))
    chart_movimientos = json.dumps({
        "labels": dias,
        "entrada": [por_dia[d]["entrada"] for d in dias],
        "salida":  [por_dia[d]["salida"]  for d in dias],
        "merma":   [por_dia[d]["merma"]   for d in dias],
        "ajuste":  [por_dia[d]["ajuste"]  for d in dias],
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

    return {
        "total_insumos": total_insumos,
        "total_criticos": total_criticos,
        "total_normales": total_normales,
        "valor_total": valor_total,
        "chart_estado": chart_estado,
        "chart_categorias": chart_categorias,
        "chart_movimientos": chart_movimientos,
        "chart_top_valor": chart_top_valor,
    }


class InventarioController:

    # ==========================================
    # DASHBOARD
    # ==========================================
    @staticmethod
    def dashboard():
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "3", "4"]:
            return redirect(url_for("routes.login"))

        if str(session["usuario_rol"]) == "3":
            return redirect(url_for("routes.cocina_graficas_inventario"))

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
            valor_total = calcular_valor_inventario(insumos)

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
    def _procesar_movimiento(tipo):
        """Logica compartida para registrar entrada, salida o merma.

        En GET muestra el formulario; en POST registra el movimiento.
        La autorizacion la garantizan los decoradores de la ruta.
        """
        if request.method == "POST":
            try:
                data = request.get_json()

                movimiento_data = {
                    "tipo": tipo,
                    "insumo_id": data["insumo_id"],
                    "cantidad": float(data["cantidad"]),
                    "usuario_id": session["usuario_id"],
                    "motivo": data.get("motivo", ""),
                }
                # El costo aplica a entradas; en salida/merma es opcional.
                if data.get("costo_unitario") not in (None, ""):
                    movimiento_data["costo_unitario"] = float(data["costo_unitario"])

                resultado = MovimientoInventario.registrar_movimiento(movimiento_data)

                if not resultado["success"]:
                    return jsonify({
                        "success": False,
                        "message": resultado.get("error", "No se pudo registrar el movimiento"),
                    }), 400

                AlertaStock.generar_alertas_automaticas()
                NotificacionSistemaController.notificar_movimiento_inventario(
                    usuario_id=session.get("usuario_id"),
                    tipo_movimiento=tipo.value,
                    nombre_insumo=data.get("nombre_insumo", "Insumo"),
                    cantidad=data["cantidad"],
                )
                return jsonify({"success": True})

            except Exception as e:
                logging.error(f"Error al registrar {tipo.value}: {e}")
                return jsonify({"success": False, "message": "Error interno del servidor"}), 500

        # GET -> formulario
        acciones = {
            TipoMovimiento.ENTRADA: "routes.inventario_registrar_entrada",
            TipoMovimiento.SALIDA: "routes.inventario_registrar_salida",
            TipoMovimiento.MERMA: "routes.inventario_registrar_merma",
        }
        return render_template(
            "inventario/movimientos/form.html",
            tipo=tipo.value,
            requiere_costo=(tipo == TipoMovimiento.ENTRADA),
            action_url=url_for(acciones[tipo]),
            insumos=Insumo.obtener_todos({"activo": True}),
            proveedores=Proveedor.obtener_todos(),
        )

    @staticmethod
    def registrar_entrada():
        return InventarioController._procesar_movimiento(TipoMovimiento.ENTRADA)

    @staticmethod
    def registrar_salida():
        return InventarioController._procesar_movimiento(TipoMovimiento.SALIDA)

    @staticmethod
    def registrar_merma():
        return InventarioController._procesar_movimiento(TipoMovimiento.MERMA)

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
                "inventario/movimientos.html",
                movimientos=movimientos,
                insumos=insumos,
                tipos_movimiento=tipos_movimiento
            )

        except Exception as e:
            logging.error(f"Error al obtener historial: {str(e)}")
            return render_template("inventario/movimientos.html", error="Error interno del servidor")
    
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
    def graficas_cocina():
        """Gráficas de inventario para rol cocina — layout cocina"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) != "3":
            return redirect(url_for("routes.login"))

        try:
            datos = _build_chart_data(
                Insumo.obtener_todos({"activo": True}),
                Insumo.obtener_stock_critico()
            )
            return render_template("cocina/graficas_inventario.html", **datos)
        except Exception as e:
            logging.error(f"Error en graficas_cocina: {e}")
            return render_template(
                "cocina/graficas_inventario.html",
                total_insumos=0, total_criticos=0, total_normales=0, valor_total=0,
                chart_estado=json.dumps({"labels": [], "data": [], "colors": []}),
                chart_top_valor=json.dumps({"labels": [], "data": []}),
                chart_categorias=json.dumps({"labels": [], "data": []}),
                chart_movimientos=json.dumps({"labels": [], "data": [], "colors": []})
            )

    @staticmethod
    def reportes():
        """Dashboard de reportes de inventario — mismas gráficas que cocina"""
        if "usuario_rol" not in session or str(session["usuario_rol"]) not in ["1", "4"]:
            return redirect(url_for("routes.login"))

        try:
            datos = _build_chart_data(
                Insumo.obtener_todos({"activo": True}),
                Insumo.obtener_stock_critico()
            )
            return render_template("inventario/reportes.html", **datos)
        except Exception as e:
            logging.error(f"Error en reportes inventario: {e}")
            empty = json.dumps({"labels": []})
            return render_template(
                "inventario/reportes.html",
                total_insumos=0, total_criticos=0,
                total_normales=0, valor_total=0,
                chart_estado=json.dumps({"labels": [], "data": [], "colors": []}),
                chart_top_valor=json.dumps({"labels": [], "data": []}),
                chart_categorias=json.dumps({"labels": [], "data": []}),
                chart_movimientos=json.dumps({"labels": [], "data": [], "colors": []})
            )

    # ==========================================
    # PREDICCIÓN (ML: consumo + reorden)
    # ==========================================
    @staticmethod
    def prediccion():
        """Pronóstico de consumo (regresión/RMSE) y reorden (clasificación/matriz)."""
        from services.inventario.prediccion_service import preparar_dataset, entrenar_y_evaluar
        try:
            insumos = Insumo.obtener_todos({"activo": True})
            movimientos = MovimientoInventario.obtener_historial({}, limit=5000)
            fechas = [m["fecha"] for m in movimientos
                      if m.get("tipo") == TipoMovimiento.SALIDA and m.get("fecha")]
            dias_ventana = ((max(fechas) - min(fechas)).days + 1) if len(fechas) >= 2 else 30
            dataset = preparar_dataset(insumos, movimientos, dias_ventana=dias_ventana, umbral_dias=7)
            resultado = entrenar_y_evaluar(dataset)
            return render_template("inventario/prediccion.html", r=resultado, dias_ventana=dias_ventana)
        except Exception as e:
            logging.error(f"Error en predicción de inventario: {e}")
            return render_template(
                "inventario/prediccion.html",
                r={"ok": False, "motivo": "Error al generar la predicción"}, dias_ventana=0
            )