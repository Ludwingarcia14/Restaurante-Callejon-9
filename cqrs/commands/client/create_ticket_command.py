from models.soporte_model import Ticket
from datetime import datetime

class CreateTicketCommand:
    def __init__(self, usuario_id: str, asunto: str, descripcion: str):
        self.usuario_id = usuario_id
        self.asunto = asunto
        self.descripcion = descripcion

    def execute(self):
        """
        Crea un nuevo ticket de soporte.
        Delega la lógica de persistencia al modelo Ticket.
        """
        # Se asume que Ticket.crear_ticket maneja la inserción en la base de datos
        Ticket.crear_ticket(self.usuario_id, self.asunto, self.descripcion)