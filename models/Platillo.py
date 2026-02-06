from models.Pedido import db

class Platillo(db.Model):
    __tablename__ = 'platillos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float, nullable=False)
    disponible = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Platillo {self.nombre}>'