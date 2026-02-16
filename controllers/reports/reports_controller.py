"""
Controlador de Reportes - Sistema Completo de Reportes
Maneja todas las rutas y lógica de reportes
"""
from flask import Blueprint, render_template, request, jsonify, make_response, redirect, url_for
from datetime import datetime, timedelta
from models.reports_model import ReportsModel
import csv
import io
import json

reports_bp = Blueprint('reports', __name__, url_prefix='/reportes')

def parse_date(date_str):
    """Convierte string de fecha a datetime"""
    if not date_str:
        return datetime.now()
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return datetime.now()

def get_default_dates():
    """Obtiene fechas por defecto (últimos 30 días)"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    return start_date, end_date

# ==========================================
# RUTAS PRINCIPALES DE REPORTES
# ==========================================

@reports_bp.route('/')
def index():
    """Página principal de reportes"""
    return render_template('reports/index.html', title='Reportes del Restaurante')

@reports_bp.route('/financieros')
def financieros():
    """Página de reportes financieros"""
    return render_template('reports/financieros.html', title='Reportes Financieros')

@reports_bp.route('/inventario')
def inventario():
    """Página de reportes de inventario"""
    return render_template('reports/inventario.html', title='Reportes de Inventario')

@reports_bp.route('/operativos')
def operativos():
    """Página de reportes operativos"""
    return render_template('reports/operativos.html', title='Reportes Operativos')

# ==========================================
# API: REPORTES FINANCIEROS
# ==========================================

@reports_bp.route('/api/ventas-por-periodo')
def api_ventas_por_periodo():
    """API: Ventas por día/semana/mes"""
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    granularidad = request.args.get('granularidad', 'dia')
    
    data = ReportsModel.ventas_por_periodo(fecha_inicio, fecha_fin, granularidad)
    return jsonify({"success": True, "data": data})

@reports_bp.route('/api/utilidad-bruta')
def api_utilidad_bruta():
    """API: Utilidad bruta"""
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    
    data = ReportsModel.utilidad_bruta(fecha_inicio, fecha_fin)
    return jsonify({"success": True, "data": data})

@reports_bp.route('/api/margen-por-producto')
def api_margen_producto():
    """API: Margen por producto"""
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    
    data = ReportsModel.margen_por_producto(fecha_inicio, fecha_fin)
    return jsonify({"success": True, "data": data})

@reports_bp.route('/api/ingresos-vs-gastos')
def api_ingresos_gastos():
    """API: Ingresos vs Gastos"""
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    
    data = ReportsModel.ingresos_vs_gastos(fecha_inicio, fecha_fin)
    return jsonify({"success": True, "data": data})

@reports_bp.route('/api/flujo-caja')
def api_flujo_caja():
    """API: Flujo de caja"""
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    
    data = ReportsModel.flujo_caja(fecha_inicio, fecha_fin)
    return jsonify({"success": True, "data": data})

# ==========================================
# API: REPORTES DE INVENTARIO
# ==========================================

@reports_bp.route('/api/consumo-por-periodo')
def api_consumo_periodo():
    """API: Consumo por período"""
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    
    data = ReportsModel.consumo_por_periodo(fecha_inicio, fecha_fin)
    return jsonify({"success": True, "data": data})

@reports_bp.route('/api/merma-acumulada')
def api_merma():
    """API: Merma acumulada"""
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    
    data = ReportsModel.merma_acumulada(fecha_inicio, fecha_fin)
    return jsonify({"success": True, "data": data})

@reports_bp.route('/api/rotacion-inventario')
def api_rotacion():
    """API: Rotación de inventario"""
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    
    data = ReportsModel.rotacion_inventario(fecha_inicio, fecha_fin)
    return jsonify({"success": True, "data": data})

@reports_bp.route('/api/insumos-costosos')
def api_insumos_costosos():
    """API: Insumos más costosos"""
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    limite = int(request.args.get('limite', 10))
    
    data = ReportsModel.insumos_mas_costosos(fecha_inicio, fecha_fin, limite)
    return jsonify({"success": True, "data": data})

@reports_bp.route('/api/stock-actual')
def api_stock():
    """API: Stock actual"""
    data = ReportsModel.stock_actual()
    return jsonify({"success": True, "data": data})

# ==========================================
# API: REPORTES OPERATIVOS
# ==========================================

@reports_bp.route('/api/rendimiento-empleado')
def api_rendimiento():
    """API: Rendimiento por empleado"""
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    
    data = ReportsModel.rendimiento_empleado(fecha_inicio, fecha_fin)
    return jsonify({"success": True, "data": data})

@reports_bp.route('/api/tiempo-servicio')
def api_tiempo_servicio():
    """API: Tiempo promedio de servicio"""
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    
    data = ReportsModel.tiempo_promedio_servicio(fecha_inicio, fecha_fin)
    return jsonify({"success": True, "data": data})

@reports_bp.route('/api/platillos-mas-vendidos')
def api_platillos_vendidos():
    """API: Platillos más vendidos"""
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    limite = int(request.args.get('limite', 10))
    
    data = ReportsModel.platillos_mas_vendidos(fecha_inicio, fecha_fin, limite)
    return jsonify({"success": True, "data": data})

@reports_bp.route('/api/platillos-menos-rentables')
def api_platillos_rentables():
    """API: Platillos menos rentables"""
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    limite = int(request.args.get('limite', 10))
    
    data = ReportsModel.platillos_menos_rentables(fecha_inicio, fecha_fin, limite)
    return jsonify({"success": True, "data": data})

# ==========================================
# API: GRÁFICOS
# ==========================================

@reports_bp.route('/api/grafico-ventas-mensual')
def api_grafico_ventas_mensual():
    """API: Gráfico de barras - Ventas por mes"""
    # Últimos 12 meses
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    data = ReportsModel.ventas_por_periodo(start_date, end_date, 'mes')
    return jsonify({"success": True, "data": data})

@reports_bp.route('/api/grafico-metodos-pago')
def api_grafico_pagos():
    """API: Gráfico pastel - Métodos de pago"""
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    
    data = ReportsModel.distribucion_metodos_pago(fecha_inicio, fecha_fin)
    return jsonify({"success": True, "data": data})

@reports_bp.route('/api/grafico-tendencia-ingresos')
def api_grafico_tendencia():
    """API: Gráfico de línea - Tendencia de ingresos"""
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    
    data = ReportsModel.tendencia_ingresos(fecha_inicio, fecha_fin)
    return jsonify({"success": True, "data": data})

# ==========================================
# EXPORTACIÓN
# ==========================================

@reports_bp.route('/exportar/csv')
def exportar_csv():
    """Exporta datos a CSV"""
    reporte = request.args.get('reporte', 'ventas')
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    
    # Obtener datos según el reporte
    if reporte == 'ventas':
        data = ReportsModel.ventas_por_periodo(fecha_inicio, fecha_fin)
        filename = 'ventas'
    elif reporte == 'inventario':
        data = ReportsModel.consumo_por_periodo(fecha_inicio, fecha_fin)
        filename = 'inventario'
    elif reporte == 'platillos':
        data = ReportsModel.platillos_mas_vendidos(fecha_inicio, fecha_fin, 100)
        filename = 'platillos'
    elif reporte == 'empleados':
        data = ReportsModel.rendimiento_empleado(fecha_inicio, fecha_fin)
        filename = 'empleados'
    else:
        data = []
        filename = 'reporte'
    
    # Crear CSV
    if not data:
        return make_response("No hay datos para exportar", 400)
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename={filename}_{datetime.now().strftime("%Y%m%d")}.csv'
    response.headers['Content-type'] = 'text/csv'
    
    return response

@reports_bp.route('/exportar/excel')
def exportar_excel():
    """Exporta datos a Excel (CSV con extensión .xls para compatibilidad)"""
    reporte = request.args.get('reporte', 'ventas')
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    
    if reporte == 'ventas':
        data = ReportsModel.ventas_por_periodo(fecha_inicio, fecha_fin)
        filename = 'ventas'
    elif reporte == 'inventario':
        data = ReportsModel.consumo_por_periodo(fecha_inicio, fecha_fin)
        filename = 'inventario'
    elif reporte == 'platillos':
        data = ReportsModel.platillos_mas_vendidos(fecha_inicio, fecha_fin, 100)
        filename = 'platillos'
    elif reporte == 'empleados':
        data = ReportsModel.rendimiento_empleado(fecha_inicio, fecha_fin)
        filename = 'empleados'
    else:
        data = []
        filename = 'reporte'
    
    if not data:
        return make_response("No hay datos para exportar", 400)
    
    # Crear HTML table compatible con Excel
    html = '''<!DOCTYPE html>
<html>
<head>
    <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #000; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
    </style>
</head>
<body>
<table>
<tr>'''
    
    # Headers
    for key in data[0].keys():
        html += f'<th>{key}</th>'
    html += '</tr>'
    
    # Data
    for row in data:
        html += '<tr>'
        for value in row.values():
            html += f'<td>{value}</td>'
        html += '</tr>'
    
    html += '</table></body></html>'
    
    response = make_response(html)
    response.headers['Content-Disposition'] = f'attachment; filename={filename}_{datetime.now().strftime("%Y%m%d")}.xls'
    response.headers['Content-type'] = 'application/vnd.ms-excel'
    
    return response

@reports_bp.route('/exportar/pdf')
def exportar_pdf():
    """Exporta datos a PDF (genera HTML imprimible)"""
    reporte = request.args.get('reporte', 'ventas')
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    
    if reporte == 'ventas':
        data = ReportsModel.ventas_por_periodo(fecha_inicio, fecha_fin)
        title = 'Reporte de Ventas'
    elif reporte == 'inventario':
        data = ReportsModel.consumo_por_periodo(fecha_inicio, fecha_fin)
        title = 'Reporte de Inventario'
    elif reporte == 'platillos':
        data = ReportsModel.platillos_mas_vendidos(fecha_inicio, fecha_fin, 100)
        title = 'Reporte de Platillos'
    elif reporte == 'empleados':
        data = ReportsModel.rendimiento_empleado(fecha_inicio, fecha_fin)
        title = 'Reporte de Empleados'
    else:
        data = []
        title = 'Reporte'
    
    return render_template('reports/pdf_template.html', 
                           title=title, 
                           data=data, 
                           fecha_inicio=fecha_inicio.strftime('%Y-%m-%d'),
                           fecha_fin=fecha_fin.strftime('%Y-%m-%d'),
                           generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# ==========================================
# RESUMEN EJECUTIVO
# ==========================================

@reports_bp.route('/resumen-ejecutivo')
def resumen_ejecutivo():
    """Página de resumen ejecutivo"""
    fecha_inicio = parse_date(request.args.get('fecha_inicio'))
    fecha_fin = parse_date(request.args.get('fecha_fin'))
    
    data = ReportsModel.resumen_ejecutivo(fecha_inicio, fecha_fin)
    return render_template('reports/resumen_ejecutivo.html', 
                           title='Resumen Ejecutivo',
                           data=data,
                           fecha_inicio=fecha_inicio.strftime('%Y-%m-%d'),
                           fecha_fin=fecha_fin.strftime('%Y-%m-%d'))
