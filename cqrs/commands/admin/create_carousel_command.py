from config.db import db
from datetime import datetime
from pymongo.errors import CollectionInvalid

class CreateCarouselCommand:
    def __init__(self, titulo, descripcion, btn_texto, btn_link, imagen_url):
        self.titulo = titulo
        self.descripcion = descripcion
        self.btn_texto = btn_texto
        self.btn_link = btn_link
        self.imagen_url = imagen_url

    def execute(self):
        try:
            # ✅ db es un objeto Database, NO una función
            mongo_db = db

            # Crear colección si no existe
            if "carousel" not in mongo_db.list_collection_names():
                mongo_db.create_collection("carousel")
                mongo_db.carousel.create_index("fecha_creacion")

            carousel_data = {
                "titulo": self.titulo,
                "descripcion": self.descripcion,
                "btn_texto": self.btn_texto,
                "btn_link": self.btn_link,
                "imagen_url": self.imagen_url,
                "activo": True,
                "fecha_creacion": datetime.utcnow()
            }

            result = mongo_db.carousel.insert_one(carousel_data)

            return result.acknowledged

        except CollectionInvalid:
            print("La colección ya existe.")
            return False

        except Exception as e:
            print(f"Error en CreateCarouselCommand (MongoDB): {e}")
            return False
