from config.db import db
from bson.objectid import ObjectId
from models.clienteModel import Cliente

class GetProfileQueries:
    @staticmethod
    def get_client_profile_data(usuario_id: str) -> dict:
        """
        Busca los datos completos del perfil del cliente y resuelve los IDs de ubicación/rol.
        """
        try:
            obj_id = ObjectId(usuario_id)
            cliente_data = Cliente.collection.find_one({"_id": obj_id})

            if cliente_data:
                # Resuelve IDs a nombres (simulando joins)
                rol = db.roles.find_one({"Rol_id": cliente_data.get("cliente_rol")})
                estado = db.estados.find_one({"id": cliente_data.get("cliente_idEstado")})
                municipio = db.municipios.find_one({"id": cliente_data.get("cliente_idMunicipio")})
                colonia = db.colonias.find_one({"id": cliente_data.get("cliente_idColonia")})

                cliente_data["usuario_rol_nombre"] = rol["Rol_nombre"] if rol else ""
                cliente_data["usuario_estado_nombre"] = estado["nombre"] if estado else ""
                cliente_data["usuario_municipio_nombre"] = municipio["nombre"] if municipio else ""
                cliente_data["usuario_colonia_nombre"] = colonia["nombre"] if colonia else ""
            
            return cliente_data
        except Exception:
            return None