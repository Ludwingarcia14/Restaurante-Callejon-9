from config.db import db
from bson.objectid import ObjectId
from typing import Dict, Any, List, Optional
from datetime import datetime

class GetAsesorQueries:
    @staticmethod
    def get_asesor_roles() -> List[Dict[str, str]]:
        """Trae los roles que pueden ser asignados a un asesor (rol 3)."""
        # INTENTA ESTO: Busca tanto el número 3 como el string "3" para asegurar
        roles_ids = [3, "3"] 
        
        roles_cursor = db.roles.find({"Rol_id": {"$in": roles_ids}})
        
        roles = []
        for r in roles_cursor:
            roles.append({
                "Rol_id": str(r.get("Rol_id")), # Usa .get() para evitar errores si falta el campo
                "Rol_nombre": r.get("Rol_nombre", "Sin nombre")
            })
        
        return roles

    @staticmethod
    def get_asesores_for_datatable(start: int, length: int, search_value: str) -> Dict[str, Any]:
        """Obtiene datos de asesores con paginación, búsqueda y resuelve nombres de ubicación."""
        
        query = {"usuario_rol": "3"}

        if search_value:
            query["$or"] = [
                {"usuario_nombre": {"$regex": search_value, "$options": "i"}},
                {"usuario_apellidos": {"$regex": search_value, "$options": "i"}},
                {"usuario_email": {"$regex": search_value, "$options": "i"}},
                {"usuario_telefono": {"$regex": search_value, "$options": "i"}},
            ]

        # Conteo total y filtrado
        total_records = db.usuarios.count_documents({"usuario_rol": "3"})
        total_filtered = db.usuarios.count_documents(query)

        cursor = db.usuarios.find(query).skip(start).limit(length).sort("created_at", -1)
        data = []

        # Mapa de IDs de ubicación a nombres (para optimizar joins en DB)
        estado_map = {e["id"]: e["nombre"] for e in db.estados.find({}, {"id": 1, "nombre": 1})}
        municipio_map = {m["id"]: m["nombre"] for m in db.municipios.find({}, {"id": 1, "nombre": 1})}
        colonia_map = {c["id"]: c["nombre"] for c in db.colonias.find({}, {"id": 1, "nombre": 1})}

        for u in cursor:
            # Resolución de nombres
            estado_nombre = estado_map.get(u.get("usuario_idEstado"), "N/A")
            municipio_nombre = municipio_map.get(u.get("usuario_idMunicipio"), "N/A")
            colonia_nombre = colonia_map.get(u.get("usuario_idColonia"), "N/A")
            rol_nombre = "Asesor"
            
            data.append({
                "_id": str(u["_id"]),
                "usuario_nombre": u.get("usuario_nombre", "N/A"),
                "usuario_apellidos": u.get("usuario_apellidos", "N/A"),
                "usuario_cp": u.get("usuario_cp", "N/A"),
                "usuario_idEstado": estado_nombre,
                "usuario_idMunicipio": municipio_nombre,
                "usuario_idColonia": colonia_nombre,
                "usuario_telefono": u.get("usuario_telefono", "N/A"),
                "usuario_correo": u.get("usuario_email", "N/A"),
                "usuario_rol": rol_nombre,
                "created_at": u.get("created_at", "N/A")
            })

        return {
            "recordsTotal": total_records,
            "recordsFiltered": total_filtered,
            "data": data
        }

    @staticmethod
    def get_asesor_for_edit_view(asesor_id: str) -> Optional[Dict[str, str]]:
        """Obtiene y formatea los datos de un asesor específico para la vista de edición."""
        try:
            asesor_obj_id = ObjectId(asesor_id)
        except:
            return None
            
        usuario = db.usuarios.find_one({"_id": asesor_obj_id, "usuario_rol": "3"})
        if not usuario:
            return None
            
        fecha = usuario.get("created_at", "")
        fecha_input = ""

        if fecha:
            # Asume que 'created_at' está en formato "YYYY-MM-DD HH:MM:SS"
            fecha_parte = fecha.split(" ")[0]
            fecha_input = fecha_parte

        # Armar datos para enviar al template
        data = {
            "_id": str(usuario["_id"]),
            "usuario_nombre": usuario.get("usuario_nombre", ""),
            "usuario_apellidos": usuario.get("usuario_apellidos", ""),
            "usuario_email": usuario.get("usuario_email", ""),
            "usuario_telefono": usuario.get("usuario_telefono", ""),
            "usuario_cp": usuario.get("usuario_cp", ""),
            "usuario_idEstado": usuario.get("usuario_idEstado"),
            "usuario_idMunicipio": usuario.get("usuario_idMunicipio"),
            "usuario_idColonia": usuario.get("usuario_idColonia"),
            "created_at": fecha_input,
            "usuario_rol": "Asesor"
        }
        return data

    @staticmethod
    def get_all_clientes_list() -> List[Dict[str, Any]]:
        """Devuelve una lista de todos los clientes para el API conteo/lista."""
        clientes_cursor = db.clientes.find({})
        lista_clientes = []
        for doc in clientes_cursor:
            doc['_id'] = str(doc['_id'])
            lista_clientes.append(doc)
        return lista_clientes