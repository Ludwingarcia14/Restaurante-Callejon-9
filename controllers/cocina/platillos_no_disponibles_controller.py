from models import db  # Asegurar import correcto
from models.PlatilloNoDisponible import PlatilloNoDisponible
from models.Platillo import Platillo


class PlatillosNoDisponiblesController:
    
    @staticmethod
    def obtener_no_disponibles():
        """Obtiene lista de platillos no disponibles activos"""
        try:
            no_disponibles = PlatilloNoDisponible.query.filter_by(activo=True).all()
            return [
                {
                    'id': p.id,
                    'platillo': p.platillo.nombre if p.platillo else 'Desconocido',
                    'razon': p.razon,
                    'fecha_registro': p.fecha_registro.strftime('%H:%M'),
                    'usuario_registro': p.usuario_registro
                }
                for p in no_disponibles
            ]
        except Exception as e:
            print(f"Error al obtener no disponibles: {e}")
            return []
    
    @staticmethod
    def marcar_no_disponible(data):
        """Marca un platillo como no disponible"""
        try:
            # ✅ CORREGIDO: Validar datos
            platillo_id = data.get('platillo_id')
            razon = data.get('razon')
            usuario_registro = data.get('usuario_registro')
            
            if not platillo_id:
                return {'success': False, 'error': 'ID del platillo es requerido'}
            
            if not razon:
                return {'success': False, 'error': 'Razón es requerida'}
            
            # ✅ CORREGIDO: Verificar existencia
            platillo = Platillo.query.get(platillo_id)
            if not platillo:
                return {'success': False, 'error': 'Platillo no encontrado'}
            
            # ✅ CORREGIDO: Evitar duplicados
            existente = PlatilloNoDisponible.query.filter_by(
                platillo_id=platillo_id,
                activo=True
            ).first()
            
            if existente:
                return {'success': False, 'error': 'El platillo ya está marcado como no disponible'}
            
            no_disponible = PlatilloNoDisponible(
                platillo_id=platillo_id,
                razon=razon,
                usuario_registro=usuario_registro
            )
            platillo.disponible = False
            
            db.session.add(no_disponible)
            db.session.commit()
            return {'success': True}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def reactivar_platillo(platillo_id):
        """Reactiva un platillo marcándolo como disponible"""
        try:
            # ✅ CORREGIDO: Validar ID
            if not platillo_id:
                return {'success': False, 'error': 'ID del platillo es requerido'}
            
            no_disponible = PlatilloNoDisponible.query.filter_by(
                platillo_id=platillo_id,
                activo=True
            ).first()
            
            if no_disponible:
                no_disponible.activo = False
            
            platillo = Platillo.query.get(platillo_id)
            if platillo:
                platillo.disponible = True
            
            db.session.commit()
            return {'success': True}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}