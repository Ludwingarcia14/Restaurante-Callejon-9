from models import db
from models.PlatilloNoDisponible import PlatilloNoDisponible
from models.Platillo import Platillo
from datetime import datetime
from extensions import socketio


class PlatillosNoDisponiblesService:
    
    @staticmethod
    def obtener_todos(page=1, per_page=20, incluir_inactivos=False):
        """Obtiene todos los registros con paginación"""
        try:
            query = PlatilloNoDisponible.query
            
            if not incluir_inactivos:
                query = query.filter_by(activo=True)
            
            # Ordenar por fecha (más reciente primero)
            query = query.order_by(PlatilloNoDisponible.fecha_registro.desc())
            
            # Paginación
            paginated = query.paginate(page=page, per_page=per_page, error_out=False)
            
            return {
                "data": [
                    {
                        'id': reg.id,
                        'platillo_id': reg.platillo_id,
                        'platillo_nombre': reg.platillo.nombre if reg.platillo else 'Desconocido',
                        'razon': reg.razon,
                        'activo': reg.activo,
                        'fecha_registro': reg.fecha_registro.strftime('%Y-%m-%d %H:%M:%S'),
                        'usuario_registro': reg.usuario_registro,
                        'fecha_reactivacion': reg.fecha_reactivacion.strftime('%Y-%m-%d %H:%M:%S') if reg.fecha_reactivacion else None,
                        'usuario_reactivacion': reg.usuario_reactivacion
                    }
                    for reg in paginated.items
                ],
                "total": paginated.total,
                "page": page,
                "per_page": per_page,
                "pages": paginated.pages
            }
        except Exception as e:
            print(f"Error en obtener_todos: {e}")
            raise
    
    @staticmethod
    def obtener_activos():
        """Obtiene solo los registros activos (actualmente no disponibles)"""
        try:
            registros = PlatilloNoDisponible.query.filter_by(activo=True).all()
            return [
                {
                    'id': reg.id,
                    'platillo_id': reg.platillo_id,
                    'platillo_nombre': reg.platillo.nombre if reg.platillo else 'Desconocido',
                    'razon': reg.razon,
                    'fecha_registro': reg.fecha_registro.strftime('%H:%M'),
                    'usuario_registro': reg.usuario_registro,
                    'tiempo_no_disponible': PlatillosNoDisponiblesService._calcular_tiempo(reg.fecha_registro)
                }
                for reg in registros
            ]
        except Exception as e:
            print(f"Error en obtener_activos: {e}")
            return []
    
    @staticmethod
    def obtener_historial():
        """Obtiene historial completo de todos los platillos que han estado no disponibles"""
        try:
            # Agrupar por platillo
            from sqlalchemy import func
            
            historial = db.session.query(
                PlatilloNoDisponible.platillo_id,
                Platillo.nombre.label('platillo_nombre'),
                func.count(PlatilloNoDisponible.id).label('veces_marcado'),
                func.sum(case((PlatilloNoDisponible.activo == True, 1), else_=0)).label('actualmente_no_disponible')
            ).join(Platillo, Platillo.id == PlatilloNoDisponible.platillo_id)\
             .group_by(PlatilloNoDisponible.platillo_id, Platillo.nombre)\
             .order_by(func.count(PlatilloNoDisponible.id).desc()).all()
            
            return [
                {
                    'platillo_id': h.platillo_id,
                    'platillo_nombre': h.platillo_nombre,
                    'veces_marcado': h.veces_marcado,
                    'actualmente_no_disponible': h.actualmente_no_disponible > 0
                }
                for h in historial
            ]
        except Exception as e:
            print(f"Error en obtener_historial: {e}")
            return []
    
    @staticmethod
    def marcar_no_disponible(platillo_id, razon, usuario_registro, usuario_id):
        """Marca un platillo como no disponible"""
        try:
            # Verificar que el platillo existe
            platillo = Platillo.query.get(platillo_id)
            if not platillo:
                return {'success': False, 'error': 'El platillo no existe'}
            
            # Verificar si ya está marcado como no disponible
            existente = PlatilloNoDisponible.query.filter_by(
                platillo_id=platillo_id,
                activo=True
            ).first()
            
            if existente:
                return {'success': False, 'error': f'El platillo "{platillo.nombre}" ya está marcado como no disponible'}
            
            # Crear registro
            no_disponible = PlatilloNoDisponible(
                platillo_id=platillo_id,
                razon=razon,
                usuario_registro=usuario_registro
            )
            
            # Actualizar platillo
            platillo.disponible = False
            
            db.session.add(no_disponible)
            db.session.commit()
            
            # Emitir evento WebSocket para actualizar en tiempo real
            socketio.emit('platillo_no_disponible', {
                'platillo_id': platillo_id,
                'platillo_nombre': platillo.nombre,
                'razon': razon,
                'usuario': usuario_registro
            }, room='cocina')
            
            return {
                'success': True, 
                'message': f'Platillo "{platillo.nombre}" marcado como no disponible',
                'data': {
                    'id': no_disponible.id,
                    'platillo': platillo.nombre,
                    'razon': razon
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def reactivar_platillo(platillo_id, usuario_id):
        """Reactivar un platillo (volver a disponible)"""
        try:
            # Buscar registro activo
            no_disponible = PlatilloNoDisponible.query.filter_by(
                platillo_id=platillo_id,
                activo=True
            ).first()
            
            if not no_disponible:
                return {'success': False, 'error': 'El platillo no está marcado como no disponible'}
            
            # Obtener nombre del usuario (podrías obtenerlo de la sesión)
            from models.Usuario import Usuario
            usuario = Usuario.query.get(usuario_id)
            usuario_nombre = usuario.nombre if usuario else 'Sistema'
            
            # Desactivar registro
            no_disponible.activo = False
            no_disponible.fecha_reactivacion = datetime.utcnow()
            no_disponible.usuario_reactivacion = usuario_nombre
            
            # Actualizar platillo
            platillo = Platillo.query.get(platillo_id)
            platillo.disponible = True
            
            db.session.commit()
            
            # Emitir evento WebSocket
            socketio.emit('platillo_reactivado', {
                'platillo_id': platillo_id,
                'platillo_nombre': platillo.nombre,
                'usuario': usuario_nombre
            }, room='cocina')
            
            return {
                'success': True,
                'message': f'Platillo "{platillo.nombre}" reactivado correctamente'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_estadisticas():
        """Obtiene estadísticas de disponibilidad"""
        try:
            total_platillos = Platillo.query.count()
            no_disponibles_actuales = PlatilloNoDisponible.query.filter_by(activo=True).count()
            total_registros = PlatilloNoDisponible.query.count()
            
            # Top razones más comunes
            from sqlalchemy import func
            top_razones = db.session.query(
                PlatilloNoDisponible.razon,
                func.count(PlatilloNoDisponible.id).label('total')
            ).group_by(PlatilloNoDisponible.razon)\
             .order_by(func.count(PlatilloNoDisponible.id).desc())\
             .limit(5).all()
            
            return {
                'total_platillos': total_platillos,
                'no_disponibles': no_disponibles_actuales,
                'porcentaje_no_disponibles': round((no_disponibles_actuales / total_platillos * 100), 2) if total_platillos > 0 else 0,
                'total_registros_historicos': total_registros,
                'top_razones': [{'razon': r[0], 'total': r[1]} for r in top_razones]
            }
        except Exception as e:
            print(f"Error en get_estadisticas: {e}")
            return {}
    
    @staticmethod
    def _calcular_tiempo(fecha_inicio):
        """Calcula tiempo transcurrido en minutos/horas"""
        if not fecha_inicio:
            return "Recién"
        
        delta = datetime.utcnow() - fecha_inicio
        minutos = int(delta.total_seconds() / 60)
        
        if minutos < 60:
            return f"{minutos} min"
        elif minutos < 1440:
            horas = minutos // 60
            return f"{horas} hora{'s' if horas > 1 else ''}"
        else:
            dias = minutos // 1440
            return f"{dias} día{'s' if dias > 1 else ''}"