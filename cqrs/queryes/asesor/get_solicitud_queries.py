from config.db import db
from bson.objectid import ObjectId

class GetSolicitudQueries:
    @staticmethod
    def get_assigned_solicitudes(asesor_id: str) -> list:
        """
        Obtiene todas las solicitudes que están asignadas a un asesor específico.
        """
        return list(db["solicitudes"].find({"asesor_id": asesor_id}))

    @staticmethod
    def get_solicitud_and_check_authorization(solicitud_id: str, asesor_id: str) -> dict:
        """
        Busca una solicitud por ID y verifica que pertenezca al asesor.
        Retorna el documento de la solicitud o None si no se encuentra o no está autorizado.
        """
        try:
            solicitud_obj_id = ObjectId(solicitud_id)
            return db["solicitudes"].find_one({
                "_id": solicitud_obj_id,
                "asesor_id": asesor_id
            })
        except Exception:
            # Captura errores si el ID de solicitud no es válido (ej. no es un ObjectId)
            return None

    @staticmethod
    def get_seguimiento_contactos(solicitud_id: str) -> list:
        """
        Obtiene todos los contactos/registros de seguimiento para una solicitud específica, ordenados por fecha.
        """
        # Nota: Asume que 'solicitud_id' en 'contactos' se guarda como string.
        return list(db["contactos"].find({
            "solicitud_id": solicitud_id
        }).sort("fecha", -1))
        
    @staticmethod
    def get_client_solicitudes(cliente_obj_id: ObjectId) -> list:
        """
        Obtiene las solicitudes de un cliente específico, ordenadas por fecha de creación descendente.
        """
        return list(db["solicitudes"].find({"cliente_id": cliente_obj_id}).sort("fecha_creacion", -1))

    @staticmethod
    def get_documentos_solicitud(solicitud_id: str) -> list:
        """
        Obtiene los documentos asociados a una solicitud específica para el proceso de validación.
        """
        return list(db["documentos"].find({"solicitud_id": solicitud_id}))

    @staticmethod
    def get_creditos_asesor(asesor_id: str) -> list:
        """
        Obtiene la cartera de créditos del asesor para la vista 'Cartera'.
        """
        return list(db["creditos"].find({"asesor_id": asesor_id}))