"""
Modelo de Inventario - Insumos, Stock, Movimientos
"""
from config.db import db
from datetime import datetime

class Insumo:
    collection = db["insumos"]
    
    @classmethod
    def find_all(cls):
        return list(cls.collection.find())
