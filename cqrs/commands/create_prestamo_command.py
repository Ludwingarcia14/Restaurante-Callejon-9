# cqrs/commands/create_prestamo_command.py
from datetime import datetime
from bson.objectid import ObjectId
from config.db import db

class CreatePrestamoHandler:
    def handle(self, data, usuario_id):
        # 1. Lógica de Negocio (que sacamos del controlador)
        cliente_id = data.get("cliente_id")
        if not cliente_id:
            raise ValueError("El cliente es obligatorio")

        nueva_clave = f"DB{datetime.now().strftime('%M%S')}"

        nuevo_prestamo = {
            "datbasicos_clave": data.get("clave") or nueva_clave,
            "cliente_id": ObjectId(cliente_id),
            "prestamo_monto": float(data.get("monto")),
            "prestamo_plazo": int(data.get("plazo")),
            "prestamo_tasa_interes": float(data.get("tasa")),
            "prestamo_motivo": data.get("motivo"),
            "prestamo_estado": "Pendiente",
            "prestamo_fecha_solicitud": datetime.strptime(data.get("fecha_solicitud"), "%Y-%m-%d"),
            "prestamo_fecha_vencimiento": datetime.strptime(data.get("fecha_vencimiento"), "%Y-%m-%d"),
            "prestamo_observaciones": data.get("observaciones"),
            "creado_por": ObjectId(usuario_id),
            "financiera_id": ObjectId(data.get("financiera_id")), # Asegúrate de pasar esto
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "deleted_at": None
        }

        # 2. Interacción con la BD
        result = db.prestamos.insert_one(nuevo_prestamo)
        return str(result.inserted_id)