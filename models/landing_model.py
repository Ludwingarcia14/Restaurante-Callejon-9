from config.db import db
from datetime import datetime
from bson.objectid import ObjectId
import re
import unicodedata


# ==========================================
# 🎠 GESTOR DEL CARRUSEL (Lo que ya tenías)
# ==========================================
class LandingManager:
    collection = db["carousel"]

    @classmethod
    def create_publication(cls, data):
        """Guarda la configuración del carrusel"""
        now = datetime.utcnow()

        document = {
            "titulo": data.get("titulo"),
            "descripcion": data.get("descripcion"),
            "tipo": data.get("tipo"),
            "imagen_url": data.get("imagen"),
            "btn_texto": data.get("btn_texto"),
            "btn_link": data.get("btn_link"),
            "activo": data.get("activo", True),
            "created_at": now,
            "updated_at": now
        }

        return cls.collection.insert_one(document)

    @classmethod
    def get_all(cls):
        """Obtiene todos los registros del carrusel"""
        return list(cls.collection.find({}).sort("created_at", -1))

    @classmethod
    def get_by_id(cls, carousel_id):
        """Obtiene un registro por ID"""
        return cls.collection.find_one({"_id": ObjectId(carousel_id)})

    @classmethod
    def delete(cls, carousel_id):
        """Elimina un registro"""
        return cls.collection.delete_one({"_id": ObjectId(carousel_id)})

    @classmethod
    def toggle_status(cls, carousel_id, status):
        """Activa / desactiva un carrusel"""
        return cls.collection.update_one(
            {"_id": ObjectId(carousel_id)},
            {"$set": {
                "activo": status,
                "updated_at": datetime.utcnow()
            }}
        )
    
    @classmethod
    def update(cls, carousel_id, data):
        """Actualiza un registro existente"""
        now = datetime.utcnow()
        
        # Preparamos los datos a actualizar
        update_data = {
            "titulo": data.get("titulo"),
            "descripcion": data.get("descripcion"),
            "tipo": data.get("tipo"),
            "btn_texto": data.get("btn_texto"),
            "btn_link": data.get("btn_link"),
            "activo": data.get("activo", True),
            "updated_at": now
        }
        
        # Si viene una nueva imagen, la actualizamos. 
        # Si no, MongoDB mantendrá la que ya existe (no la sobrescribimos con None).
        if data.get("imagen"):
            update_data["imagen_url"] = data.get("imagen")

        return cls.collection.update_one(
            {"_id": ObjectId(carousel_id)},
            {"$set": update_data}
        )

# ==========================================
# 📄 GESTOR DE PÁGINAS (Lo que faltaba)
# ==========================================
# ==========================================
# 📄 GESTOR DE PÁGINAS (Constructor Web)
# ==========================================
class PageManager:
    collection = db["pages"] 

    @staticmethod
    def slugify(text):
        if not text: return ""
        slug = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
        slug = re.sub(r"[^\w\s-]", "", slug).lower()
        return re.sub(r"[-\s]+", "-", slug).strip("-")

    @classmethod
    def create_skeleton(cls, data):
        """Crea la estructura base si no existe."""
        now = datetime.utcnow()
        titulo = data.get("titulo")
        slug = data.get("slug") # Si ya viene calculado, lo usamos

        # Si no hay slug, lo generamos del título
        if not slug:
            slug = cls.slugify(titulo)

        # Validar unicidad
        base_slug = slug
        counter = 1
        while cls.collection.find_one({"slug": slug, "tipo": data.get("tipo")}):
            slug = f"{base_slug}-{counter}"
            counter += 1

        document = {
            "titulo": titulo,
            "tipo": data.get("tipo"),
            "slug": slug,
            "contenido": [], 
            "activo": False,
            "created_at": now,
            "updated_at": now
        }
        return cls.collection.insert_one(document)

    @classmethod
    def update_content(cls, page_id, bloques_json):
        """Guarda el diseño del editor"""
        return cls.collection.update_one(
            {"_id": ObjectId(page_id)},
            {"$set": {
                "contenido": bloques_json,
                "activo": True,
                "updated_at": datetime.utcnow()
            }}
        )

    @classmethod
    def get_by_id(cls, page_id):
        return cls.collection.find_one({"_id": ObjectId(page_id)})
    
    @classmethod
    def get_page_by_slug(cls, tipo, slug):
        """Busca por Slug y Tipo (Para la API pública)"""
        return cls.collection.find_one(
            {"tipo": tipo, "slug": slug},
            {"_id": 0} # Excluimos ID para evitar error de serialización JSON
        )