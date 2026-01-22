from config.db import db
from datetime import datetime
from bson.objectid import ObjectId

class Cliente:
    # 1. Apunta a la colección 'cliente'
    collection = db["clientes"]

    # 2. El constructor __init__ con todos los campos de 'cliente'
    def __init__(self, cliente_idUsuario=None, cliente_idFinanciera=None,
                 cliente_idAsesor=None, cliente_nombre=None, cliente_apellidos=None,
                 cliente_telefono=None, cliente_email=None, cliente_rol=None,
                 cliente_idEstado=None, cliente_idMunicipio=None, cliente_idColonia=None,
                 cliente_cp=None, cliente_fechaN=None, cliente_persona=None,
                 cliente_url=None, 
                 cliente_status_session=None, # <--- 1. VALOR POR DEFECTO APLICADO
                 cliente_status=1, # <--- 1. VALOR POR DEFECTO APLICADO
                 cliente_status_documentos='pendiente_documentos', # <--- 1. VALOR POR DEFECTO APLICADO
                 cliente_statusession=False,
                 cliente_tokensession=None, cliente_token=None, cliente_permisos=None,
                 cliente_clave=None,
                 created_at=None, updated_at=None, _id=None):
        
        self._id = _id
        self.cliente_idUsuario = cliente_idUsuario
        self.cliente_idFinanciera = cliente_idFinanciera
        self.cliente_idAsesor = cliente_idAsesor
        self.cliente_nombre = cliente_nombre
        self.cliente_apellidos = cliente_apellidos
        self.cliente_telefono = cliente_telefono
        self.cliente_email = cliente_email
        self.cliente_rol = cliente_rol
        self.cliente_idEstado = cliente_idEstado
        self.cliente_idMunicipio = cliente_idMunicipio
        self.cliente_idColonia = cliente_idColonia
        self.cliente_cp = cliente_cp
        self.cliente_fechaN = cliente_fechaN
        self.cliente_persona = cliente_persona
        self.cliente_url = cliente_url
        self.cliente_status_session = cliente_status_session
        self.cliente_status = cliente_status # (Esta línea ya la tenías, está perfecta)
        self.cliente_status_documentos = cliente_status_documentos # (Esta línea ya la tenías, está perfecta)
        self.cliente_statusession = cliente_statusession
        self.cliente_tokensession = cliente_tokensession
        self.cliente_token = cliente_token
        self.cliente_permisos = cliente_permisos
        self.cliente_clave = cliente_clave
        
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    # 3. El método to_dict para guardar en MongoDB
    def to_dict(self):
        """Convierte el objeto Cliente a un diccionario para MongoDB."""
        return {
            "cliente_idUsuario": self.cliente_idUsuario,
            "cliente_idFinanciera": self.cliente_idFinanciera,
            "cliente_idAsesor": self.cliente_idAsesor,
            "cliente_nombre": self.cliente_nombre,
            "cliente_apellidos": self.cliente_apellidos,
            "cliente_telefono": self.cliente_telefono,
            "cliente_email": self.cliente_email,
            "cliente_rol": self.cliente_rol,
            "cliente_idEstado": self.cliente_idEstado,
            "cliente_idMunicipio": self.cliente_idMunicipio,
            "cliente_idColonia": self.cliente_idColonia,
            "cliente_cp": self.cliente_cp,
            "cliente_fechaN": self.cliente_fechaN,
            "cliente_persona": self.cliente_persona,
            "cliente_url": self.cliente_url,
            "cliente_status_revision": self.cliente_status_session,
            "cliente_status": self.cliente_status, # (Esta línea ya la tenías, está perfecta)
            "cliente_status_documentos": self.cliente_status, # (Esta línea ya la tenías, está perfecta)
            "cliente_statusession": self.cliente_statusession,
            "cliente_tokensession": self.cliente_tokensession,
            "cliente_token": self.cliente_token,
            "cliente_permisos": self.cliente_permisos,
            "cliente_clave": self.cliente_clave,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    # 4. Métodos CRUD (siguiendo el patrón de tu clase Usuario)
    
    @classmethod
    def find_by_email(cls, email):
        # Adaptado para buscar en 'cliente_email'
        return cls.collection.find_one({"cliente_email": email})

    @classmethod
    def find_by_id(cls, id):
        return cls.collection.find_one({"_id": ObjectId(id)})

    @classmethod
    def create(cls, data):
        # Aseguramos el valor por defecto al crear en la DB
        data["cliente_status"] = data.get("cliente_status", "pendiente_documentos") # <--- 2. VALOR POR DEFECTO APLICADO
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        return cls.collection.insert_one(data)

    @classmethod
    def update(cls, id, data):
        data["updated_at"] = datetime.utcnow()
        return cls.collection.update_one({"_id": ObjectId(id)}, {"$set": data})

    @classmethod
    def delete(cls, id):
        return cls.collection.delete_one({"_id": ObjectId(id)})

    # 5. Método _from_mongo_doc (simplificado, sin lógica 2FA)
    
    @classmethod
    def _from_mongo_doc(cls, doc):
        """Convierte un documento de MongoDB (dict) en una instancia de Cliente."""
        if not doc:
            return None
        
        # Como los campos de 'cliente' no tienen nombres especiales (como '2fa_'),
        # podemos pasar el documento directamente al constructor.
        return cls(**doc)