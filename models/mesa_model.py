"""
Modelo de Mesas - Estado y Asignación
"""
from config.db import db

class Mesa:
    collection = db["mesas"]
    
    @classmethod
    def find_all(cls):
        return list(cls.collection.find())
