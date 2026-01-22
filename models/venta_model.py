"""
Modelo de Ventas - Comandas, Ventas, Pagos
"""
from config.db import db
from datetime import datetime

class Venta:
    collection = db["ventas"]
    
    @classmethod
    def find_all(cls):
        return list(cls.collection.find())
