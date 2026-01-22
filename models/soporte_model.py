# models/soporte_model.py
from config.db import db
from bson.objectid import ObjectId
from datetime import datetime

class Ticket:
    collection = db.tickets

    @staticmethod
    def crear_ticket(usuario_id, asunto, descripcion):
        ticket = {
            "usuario_id": ObjectId(usuario_id),
            "asunto": asunto,
            "descripcion": descripcion,
            "estado": "Pendiente",
            "fecha": datetime.utcnow()
        }
        return Ticket.collection.insert_one(ticket)

    @staticmethod
    def obtener_tickets(usuario_id):
        return list(Ticket.collection.find({"usuario_id": ObjectId(usuario_id)}).sort("fecha", -1))


class FAQ:
    collection = db.faq

    @staticmethod
    def obtener_faq():
        return list(FAQ.collection.find().sort("orden", 1))
