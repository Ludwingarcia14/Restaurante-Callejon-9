"""
Query para obtener todos los eventos del calendario.
"""
from config.db import db
from flask import jsonify

class GetCalendarEventsQuery:
    """
    Recupera todos los eventos de la colección 'eventos'.
    """
    @staticmethod
    def execute():
        """
        Ejecuta la consulta y retorna la lista de eventos.

        Returns:
            tuple: (lista de eventos, error)
        """
        try:
            # Recuperar todos los eventos, excluyendo el _id para la serialización
            eventos = list(db.eventos.find({}, {"_id": 0})) 
            return eventos, None
        except Exception as e:
            return None, str(e)