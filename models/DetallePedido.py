from models.Pedido import db

class DetallePedido(db.Model):
    __tablename__ = 'detalles_pedido'
    
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    platillo_id = db.Column(db.Integer, db.ForeignKey('platillos.id'), nullable=False)
    cantidad = db.Column(db.Integer, default=1)
    notas_especiales = db.Column(db.Text, nullable=True)  # Alergias, sin ingredientes, etc.
    estado_preparacion = db.Column(db.String(20), default='no_iniciado')  # no_iniciado, preparando, listo
    
    # Relaciones
    platillo = db.relationship('Platillo', backref='detalles_pedido')
    
    def __repr__(self):
        return f'<DetallePedido {self.id}>'