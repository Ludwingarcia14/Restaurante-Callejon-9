from models.Pedido import db
from models.PlatilloNoDisponible import PlatilloNoDisponible
from models.Platillo import Platillo

class PlatillosNoDisponiblesController:
    
    @staticmethod
    def obtener_no_disponibles():
        """Obtiene lista de platillos no disponibles activos"""
        no_disponibles = PlatilloNoDisponible.query.filter_by(activo=True).all()
        return [
            {
                'id': p.id,
                'platillo': p.platillo.nombre,
                'razon': p.razon,
                'fecha_registro': p.fecha_registro.strftime('%H:%M'),
                'usuario_registro': p.usuario_registro
            }
            for p in no_disponibles
        ]
    
    @staticmethod
    def marcar_no_disponible(data):
        """Marca un platillo como no disponible"""
        try:
            no_disponible = PlatilloNoDisponible(
                platillo_id=data.get('platillo_id'),
                razon=data.get('razon'),
                usuario_registro=data.get('usuario_registro')
            )
            platillo = Platillo.query.get(data.get('platillo_id'))
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
            no_disponible = PlatilloNoDisponible.query.filter_by(
                platillo_id=platillo_id,
                activo=True
            ).first()
            
            if no_disponible:
                no_disponible.activo = False
            
            platillo = Platillo.query.get(platillo_id)
            platillo.disponible = True
            
            db.session.commit()
            return {'success': True}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}