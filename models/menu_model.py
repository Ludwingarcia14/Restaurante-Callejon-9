"""
Modelo de Menú - Platillos, Categorías, Recetas
"""
from config.db import db
from datetime import datetime
from bson.objectid import ObjectId

class Platillo:
    collection = db["platillos"]
    
    @classmethod
    def find_all(cls):
        return list(cls.collection.find())
    
    @classmethod
    def find_by_id(cls, id):
        return cls.collection.find_one({"_id": ObjectId(id)})
