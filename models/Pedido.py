from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_pedido = db.Column(db.String(50), unique=True, nullable=False)
    numero_mesa = db.Column(db.Integer, nullable=False)
    hora_entrada = db.Column(db.DateTime, default=datetime.now)
    usuario_registro = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, preparacion, listo, entregado
    total_cuenta = db.Column(db.Float, default=0.0)
    fecha_creacion = db.Column(db.DateTime, default=datetime.now)
    
    # Relaciones
    detalles = db.relationship('DetallePedido', backref='pedido', lazy=True, cascade='all, delete-orphan')
    
    def minutos_esperando(self):
        delta = datetime.now() - self.hora_entrada
        return int(delta.total_seconds() / 60)
    
    def __repr__(self):
        return f'<Pedido {self.numero_pedido}>'