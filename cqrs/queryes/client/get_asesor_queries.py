from config.db import db
from bson.objectid import ObjectId
from typing import Tuple, Optional, List

class GetAsesorQueries:
    @staticmethod
    def get_assigned_asesor_info_and_citas(cliente_id: str) -> Tuple[Optional[dict], List[dict]]:
        """
        Busca el asesor asignado al cliente, sus datos de contacto y las citas asociadas.
        
        Retorna una tupla: (datos_recientes_asesor, lista_citas)
        """
        try:
            cliente_obj_id = ObjectId(cliente_id)
        except Exception:
            return None, []
        
        # 1. Buscar el cliente en la colección "clientes" (necesario para el join)
        cliente = db.clientes.find_one({"_id": cliente_obj_id})
        if not cliente:
            return None, []

        # 2. Buscar relación en "asesor_asignado" usando el cliente._id
        asignacion = db.asesor_asignado.find_one({"cliente_id": cliente["_id"]})
        if not asignacion:
            return None, []

        # 3. Buscar el asesor en la colección "usuarios" (usando el ID de la asignación)
        asesor_id = asignacion.get("asesor_id")
        try:
            asesor = db.usuarios.find_one({"_id": ObjectId(asesor_id)})
        except Exception:
            asesor = None
            
        if not asesor:
            return None, []

        # 4. Preparar los datos del asesor para el template
        reciente = {
            "nombre_asesor": f"{asesor.get('usuario_nombre', '')} {asesor.get('usuario_apellidos', '')}",
            "telefono_asesor": asesor.get("usuario_telefono", "-"),
            "correo_asesor": asesor.get("usuario_email", "-"),
            "asesor_id": asesor_id # ID necesario para buscar citas
        }
        
        # 5. Buscar citas asociadas al asesor
        try:
            citas = list(db.citas.find({"asesor_id": ObjectId(asesor_id)}))
        except Exception:
            citas = []

        return reciente, citas