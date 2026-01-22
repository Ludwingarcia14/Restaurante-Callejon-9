from config.db import db
from bson.objectid import ObjectId
from typing import Optional

class GetDocumentQueries:
    @staticmethod
    def get_documento_fisica(usuario_obj_id: ObjectId) -> Optional[dict]:
        """
        Busca el único registro de documentos para Persona Física asociados al cliente.
        """
        # La colección debe ser db.documentofisica (donde el command guarda)
        return db.documentofisica.find_one({"usuario_id": usuario_obj_id})

    @staticmethod
    def get_documento_moral(usuario_obj_id: ObjectId) -> Optional[dict]:
        """
        Busca el único registro de documentos para Persona Moral asociados al cliente.
        """
        # La colección debe ser db.documentomoral (donde el command guarda)
        return db.documentomoral.find_one({"usuario_id": usuario_obj_id})

    # Nota: No incluimos get_documentos_solicitud aquí ya que esa consulta pertenece al módulo GetSolicitudQueries