from config.db import db
from datetime import datetime
from bson.objectid import ObjectId

class Usuario:
    collection = db["usuarios"]

    def __init__(self, usuario_id=None, usuario_nombre=None, usuario_apellidos=None,
                 usuario_telefono=None, usuario_email=None, usuario_clave=None,
                 usuario_foto=None, usuario_rol=None, usuario_idEstado=None,
                 usuario_idMunicipio=None, usuario_idColonia=None, usuario_cp=None,
                 usuario_idFinanciera=None, 
                 usuario_tipo_asesor=None, # <--- 1. AÑADIDO EN EL CONSTRUCTOR
                 usuario_status=None, usuario_token=None,
                 usuario_tokensession=None, usuario_permisos=None,
                 # === NUEVOS CAMPOS 2FA EN EL CONSTRUCTOR (Usamos 'two_factor_' para Python) ===
                 two_factor_enabled=False, two_factor_tipo=None, 
                 two_factor_secret=None, two_factor_telefono=None,
                 # ==============================================================================
                 created_at=None, updated_at=None, _id=None):
        self._id = _id
        self.usuario_id = usuario_id
        self.usuario_nombre = usuario_nombre
        self.usuario_apellidos = usuario_apellidos
        self.usuario_telefono = usuario_telefono
        self.usuario_email = usuario_email
        self.usuario_clave = usuario_clave
        self.usuario_foto = usuario_foto
        self.usuario_rol = usuario_rol
        self.usuario_idEstado = usuario_idEstado
        self.usuario_idMunicipio = usuario_idMunicipio
        self.usuario_idColonia = usuario_idColonia
        self.usuario_cp = usuario_cp
        self.usuario_idFinanciera = usuario_idFinanciera
        self.usuario_tipo_asesor = usuario_tipo_asesor # <--- 2. AÑADIDO COMO ATRIBUTO
        self.usuario_status = usuario_status
        self.usuario_token = usuario_token
        self.usuario_tokensession = usuario_tokensession
        self.usuario_permisos = usuario_permisos
        
        # === INICIALIZACIÓN DE ATRIBUTOS 2FA ===
        self.two_factor_enabled = two_factor_enabled
        self.two_factor_tipo = two_factor_tipo
        self.two_factor_secret = two_factor_secret
        self.two_factor_telefono = two_factor_telefono
        # ======================================
        
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    # 📌 Convierte el objeto a dict para MongoDB
    def to_dict(self):
        return {
            "usuario_id": self.usuario_id,
            "usuario_nombre": self.usuario_nombre,
            "usuario_apellidos": self.usuario_apellidos,
            "usuario_telefono": self.usuario_telefono,
            "usuario_email": self.usuario_email,
            "usuario_clave": self.usuario_clave,
            "usuario_foto": self.usuario_foto,
            "usuario_rol": self.usuario_rol,
            "usuario_idEstado": self.usuario_idEstado,
            "usuario_idMunicipio": self.usuario_idMunicipio,
            "usuario_idColonia": self.usuario_idColonia,
            "usuario_cp": self.usuario_cp,
            "usuario_idFinanciera": self.usuario_idFinanciera,
            "usuario_tipo_asesor": self.usuario_tipo_asesor, # <--- 3. AÑADIDO AL DICCIONARIO
            "usuario_status": self.usuario_status,
            "usuario_token": self.usuario_token,
            "usuario_tokensession": self.usuario_tokensession,
            "usuario_permisos": self.usuario_permisos,
            
            # === CAMPOS 2FA QUE SE GUARDARÁN EN MONGODB ===
            "2fa_enabled": self.two_factor_enabled,
            "2fa_tipo": self.two_factor_tipo,
            "2fa_secret": self.two_factor_secret,
            "2fa_telefono": self.two_factor_telefono,
            # ==============================================
            
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

 # --- Métodos CRUD ---
    @classmethod
    def find_by_email(cls, email):
        return cls.collection.find_one({"usuario_email": email})

    @classmethod
    def find_by_id(cls, id):
        return cls.collection.find_one({"_id": ObjectId(id)})

    # (Nota: Tienes métodos duplicados, he modificado el segundo 'create')
    @classmethod
    def create(cls, data):
        # Asegurarse de que los nuevos campos estén en la data si se usa create directamente
        data["2fa_enabled"] = data.get("2fa_enabled", False)
        data["2fa_tipo"] = data.get("2fa_tipo", None)
        data["2fa_secret"] = data.get("2fa_secret", None)
        data["2fa_telefono"] = data.get("2fa_telefono", None)
        data["usuario_tipo_asesor"] = data.get("usuario_tipo_asesor", "interno") # <--- 4. AÑADIDO PARA EL MÉTODO CREATE
        
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

    # === NUEVO MÉTODO DE CLASE PRIVADO PARA MAPEO ===
    @classmethod
    def _from_mongo_doc(cls, doc):
        """Convierte un documento de MongoDB (dict) en una instancia de Usuario, 
           manejando el mapeo de los campos 2FA."""
        if not doc:
            return None
        
        # Mapear los campos de MongoDB con guion bajo ('2fa_enabled') a atributos de Python con CamelCase ('two_factor_enabled')
        kwargs = {}
        for key, value in doc.items():
            if key.startswith('2fa_'):
                # Convierte '2fa_enabled' a 'two_factor_enabled' para el constructor
                python_key = 'two_factor_' + key[4:] 
                kwargs[python_key] = value
            else:
                kwargs[key] = value
                
        return cls(**kwargs)

    # (Aquí estaban los métodos create/update/delete duplicados)
    # ...

    # === MÉTODO ESPECÍFICO DE CLASE PARA 2FA (USADO POR EL CONTROLADOR) ===
    @classmethod
    def update_2fa_status(cls, user_id, is_enabled, tipo=None, secret=None, telefono=None):
        """Actualiza el estado completo de 2FA en la base de datos."""
        data = {
            "2fa_enabled": is_enabled,
            "2fa_tipo": tipo,
            "2fa_secret": secret,
            "2fa_telefono": telefono,
            "updated_at": datetime.utcnow()
        }
        return cls.collection.update_one({"_id": ObjectId(user_id)}, {"$set": data})
    # =========================================================================