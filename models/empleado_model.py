"""
Modelo de Usuario - Sistema de Roles para Restaurante
"""
from config.db import db
from datetime import datetime
from bson.objectid import ObjectId

class Usuario:
    collection = db["usuarios"]

    def __init__(self, _id=None, **kwargs):
        self._id = _id
        self.data = kwargs

    def to_dict(self):
        """Convierte el objeto a dict para MongoDB"""
        return self.data

    # ==========================================
    # MÉTODOS DE CONSULTA (Queries)
    # ==========================================
    
    @classmethod
    def find_by_email(cls, email):
        """Busca un usuario por email"""
        return cls.collection.find_one({"usuario_email": email})

    @classmethod
    def find_by_id(cls, id):
        """Busca un usuario por ID"""
        return cls.collection.find_one({"_id": ObjectId(id)})
    
    @classmethod
    def find_by_rol(cls, rol):
        """Obtiene todos los usuarios de un rol específico"""
        return list(cls.collection.find({"usuario_rol": str(rol)}))
    
    @classmethod
    def find_activos(cls):
        """Obtiene todos los usuarios activos"""
        return list(cls.collection.find({"usuario_status": 1}))

    # ==========================================
    # MÉTODOS DE COMANDO (Commands)
    # ==========================================
    
    @classmethod
    def create(cls, data):
        """Crea un nuevo usuario"""
        data["created_at"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        data["updated_at"] = datetime.utcnow()
        return cls.collection.insert_one(data)

    @classmethod
    def update(cls, id, data):
        """Actualiza un usuario existente"""
        data["updated_at"] = datetime.utcnow()
        return cls.collection.update_one(
            {"_id": ObjectId(id)}, 
            {"$set": data}
        )

    @classmethod
    def delete(cls, id):
        """Elimina un usuario (soft delete)"""
        return cls.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "usuario_status": 0,
                "updated_at": datetime.utcnow()
            }}
        )

    @classmethod
    def update_session_token(cls, user_id, token, status):
        """Actualiza el token de sesión y status al hacer login/logout"""
        return cls.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "usuario_tokensession": token,
                "usuario_status": status,
                "updated_at": datetime.utcnow()
            }}
        )

    @classmethod
    def update_2fa_status(cls, user_id, is_enabled, tipo=None, secret=None, telefono=None):
        """Actualiza el estado de 2FA"""
        return cls.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "2fa_enabled": is_enabled,
                "2fa_tipo": tipo,
                "2fa_secret": secret,
                "2fa_telefono": telefono,
                "updated_at": datetime.utcnow()
            }}
        )

    # ==========================================
    # HELPERS PARA PERFILES ESPECÍFICOS
    # ==========================================
    
    @staticmethod
    def get_perfil_mesero(usuario_doc):
        """Extrae el perfil de mesero del documento"""
        if not usuario_doc or usuario_doc.get("usuario_rol") != "2":
            return None
        
        return {
            "numero_empleado": usuario_doc.get("mesero_numero"),
            "turno": usuario_doc.get("mesero_turno"),
            "mesas_asignadas": usuario_doc.get("mesero_mesas", []),
            "puede_cerrar_cuenta": usuario_doc.get("mesero_puede_cerrar_cuenta", False),
            "puede_aplicar_descuento": usuario_doc.get("mesero_puede_aplicar_descuento", False),
            "propinas": {
                "sugerida": usuario_doc.get("mesero_propina_sugerida", 10),
                "acumulada_dia": usuario_doc.get("mesero_propina_acumulada_dia", 0)
            },
            "rendimiento": {
                "ventas_promedio_dia": usuario_doc.get("mesero_ventas_promedio_dia", 0),
                "calificacion_cliente": usuario_doc.get("mesero_calificacion_cliente", 0)
            }
        }
    
    @staticmethod
    def get_perfil_cocina(usuario_doc):
        """Extrae el perfil de cocina del documento"""
        if not usuario_doc or usuario_doc.get("usuario_rol") != "3":
            return None
        
        return {
            "numero_empleado": usuario_doc.get("cocina_numero"),
            "puesto": usuario_doc.get("cocina_puesto"),
            "area": usuario_doc.get("cocina_area"),
            "turno": usuario_doc.get("cocina_turno"),
            "especialidad": usuario_doc.get("cocina_especialidad", []),
            "puede_modificar_menu": usuario_doc.get("cocina_puede_modificar_menu", False),
            "puede_ver_recetas_completas": usuario_doc.get("cocina_puede_ver_recetas_completas", False),
            "certificaciones": usuario_doc.get("cocina_certificaciones", [])
        }
    @staticmethod
    def get_perfil_inventario(usuario_doc):
        """Extrae el perfil de inventario del documento"""
        if not usuario_doc or usuario_doc.get("usuario_rol") != "4":
            return None
        
        return {
            "numero_empleado": usuario_doc.get("inventario_numero"),
            "turno": usuario_doc.get("inventario_turno"),
            "areas_responsables": usuario_doc.get("inventario_areas_responsables", []),
            "puede_registrar_entradas": usuario_doc.get("inventario_puede_registrar_entradas", False),
            "puede_registrar_salidas": usuario_doc.get("inventario_puede_registrar_salidas", False),
            "puede_realizar_ajustes": usuario_doc.get("inventario_puede_realizar_ajustes", False),
            "gestiona_proveedores": usuario_doc.get("inventario_gestiona_proveedores", False),
            "recibe_alertas_stock": usuario_doc.get("inventario_recibe_alertas_stock", True)
        }


# ==========================================
# CLASE HELPER PARA PERMISOS
# ==========================================

class RolPermisos:
    """
    Define los permisos y accesos por defecto para cada rol
    """
    PERMISOS = {
        "1": {  # Administración
            "nombre": "Administrador",
            "modulos": ["dashboard", "menu", "inventario", "ventas", "reportes", "empleados", "configuracion"],
            "puede_crear": True,
            "puede_editar": True,
            "puede_eliminar": True,
            "puede_ver_reportes": True,
            "acceso_finanzas": True,
            "autoriza_descuentos": True
        },
        "2": {  # Mesero
            "nombre": "Mesero",
            "modulos": ["dashboard", "comandas", "mesas", "clientes"],
            "puede_crear": True,
            "puede_editar": True,
            "puede_eliminar": False,
            "puede_ver_reportes": False,
            "puede_cerrar_cuenta": True,
            "gestiona_propinas": True
        },
        "3": {  # Cocina
            "nombre": "Cocina",
            "modulos": ["dashboard", "comandas", "inventario_consulta"],
            "puede_crear": False,
            "puede_editar": False,
            "puede_eliminar": False,
            "puede_ver_reportes": False,
            "puede_modificar_menu": False,
            "ver_comandas_activas": True
        },
    
        "4": {  # Inventario/Almacén
            "nombre": "Encargado de Inventario",
            "modulos": ["dashboard", "inventario", "proveedores", "reportes_inventario"],
            "puede_crear": True,
            "puede_editar": True,
            "puede_eliminar": False,
            "puede_ver_reportes": True,
            "registra_entradas": True,
            "registra_salidas": True,
            "registra_ajustes": True,
            "gestiona_proveedores": True,
            "ver_costos": True,
            "recibe_alertas_stock": True
        }
}
    
    @classmethod
    def get_permisos(cls, rol):
        """Obtiene los permisos de un rol"""
        return cls.PERMISOS.get(str(rol), {})
    
    @classmethod
    def tiene_permiso(cls, rol, permiso):
        """Verifica si un rol tiene un permiso específico"""
        permisos_rol = cls.get_permisos(str(rol))
        return permisos_rol.get(permiso, False)
    
    @classmethod
    def puede_acceder_modulo(cls, rol, modulo):
        """Verifica si un rol puede acceder a un módulo"""
        permisos_rol = cls.get_permisos(str(rol))
        return modulo in permisos_rol.get("modulos", [])
    
    @classmethod
    def get_nombre_rol(cls, rol):
        """Obtiene el nombre legible del rol"""
        permisos_rol = cls.get_permisos(str(rol))
        return permisos_rol.get("nombre", "Desconocido")