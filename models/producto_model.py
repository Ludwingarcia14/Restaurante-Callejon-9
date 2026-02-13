# models/producto_model.py
from config.db import db

class Producto:
    @staticmethod
    def obtener_todo():
        # Buscamos en la colección 'productos'
        cursor = db.productos.find({"estado": "activo"})
        productos = []
        for p in cursor:
            productos.append({
                "_id": str(p["_id"]), # Importante convertir a string para JSON
                "nombre": p.get("nombre", "Sin nombre"),
                "precio": float(p.get("precio", 0)),
                "categoria": p.get("categoria", "General")
            })
        return productos