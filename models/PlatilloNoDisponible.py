from datetime import datetime
from models.Pedido import db

class PlatilloNoDisponible(db.Model):
    __tablename__ = 'platillos_no_disponibles'
    
    id = db.Column(db.Integer, primary_key=True)
    platillo_id = db.Column(db.Integer, db.ForeignKey('platillos.id'), nullable=False)
    razon = db.Column(db.String(200), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)
    usuario_registro = db.Column(db.String(100), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    
    # Relación
    platillo = db.relationship('Platillo', backref='no_disponibles')
    
    def __repr__(self):
        return f'<PlatilloNoDisponible {self.platillo_id}>'