# cqrs/queries/handlers/geo_handler.py

from bson import ObjectId
from config.db import db

class GeoQueryHandler:
    def __init__(self, db_accessor):
        self.db = db_accessor 

    def _convert_to_objectid(self, id_value):
        """Intenta convertir un string de ID a ObjectId si es válido para MongoDB."""
        if isinstance(id_value, str) and ObjectId.is_valid(id_value):
            return ObjectId(id_value)
        return id_value

    def get_estados(self):
        """Extrae la lista de estados."""
        estados = self.db.estados.find()
        return [{"id": str(e["id"]), "nombre": e["nombre"]} for e in estados]

    def get_municipios(self, estado_id):
        """Extrae la lista de municipios de un estado. *Corregido para manejar ObjectId*"""
        # Convertir el ID de entrada a ObjectId para la consulta a la BD
        query_id = self._convert_to_objectid(estado_id)
        
        # La consulta ahora usa el tipo de dato correcto (ObjectId)
        municipios = db.municipios.find({"estado": query_id})
        return [{"id": str(m["id"]), "nombre": m["nombre"]} for m in municipios]

    def get_colonias(self, municipio_id):
        """Extrae la lista de colonias de un municipio. *Corregido para manejar ObjectId*"""
        # Convertir el ID de entrada a ObjectId para la consulta a la BD
        query_id = self._convert_to_objectid(municipio_id)
        
        # La consulta ahora usa el tipo de dato correcto (ObjectId)
        colonias = self.db.colonias.find({"municipio": query_id})
        return [
            {"id": str(c["id"]), "nombre": c["nombre"], "codigo_postal": c["codigo_postal"]}
            for c in colonias
        ]

    def get_cp_data(self, cp):
        """Busca colonia por CP y devuelve datos geográficos completos. *Corregido para manejar referencias por _id*"""
        colonia = self.db.colonias.find_one({"codigo_postal": cp})
        if not colonia:
            return None

        # 1. Buscar municipio. Se busca el campo 'municipio' o 'municipio_id' y se convierte a ObjectId para buscar por '_id'.
        municipio_id_raw = colonia.get("municipio_id") or colonia.get("municipio")
        query_municipio_id = self._convert_to_objectid(municipio_id_raw)
        
        # Se busca por el campo primario _id, el estándar para referencias en MongoDB
        municipio = self.db.municipios.find_one({"_id": query_municipio_id})
        
        if not municipio:
            return None

        # 2. Buscar estado. Se busca el campo 'estado' o 'estado_id' y se convierte a ObjectId para buscar por '_id'.
        estado_id_raw = municipio.get("estado_id") or municipio.get("estado")
        query_estado_id = self._convert_to_objectid(estado_id_raw)
        
        # Se busca por el campo primario _id
        estado = self.db.estados.find_one({"_id": query_estado_id})

        if not estado:
            return None 

        return {
            "estado": {"id": str(estado["id"]), "nombre": estado["estado_nombre"]},
            "municipio": {"id": str(municipio["id"]), "nombre": municipio["municipio_nombre"]},
            "colonia": {"id": str(colonia["id"]), "nombre": colonia["colonia_nombre"], "codigo_postal": cp}
        }