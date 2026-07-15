"""
Modelo de Menú - Platillos, Categorías, Recetas
"""
from config.db import db
from datetime import datetime
from bson.objectid import ObjectId

class Categoria:
    collection = db["categorias_menu"]
    
    # Mapeo de categorías a nombres
    NOMBRE_CATEGORIAS = {
        'entrada': 'Entrada',
        'plato_fuerte': 'Plato Fuerte',
        'bebida': 'Bebida',
        'postre': 'Postre',
        'especial': 'Especial'
    }
    
    @classmethod
    def find_all(cls):
        """Obtiene todas las categorías"""
        return list(cls.collection.find().sort('nombre', 1))
    
    @classmethod
    def find_by_id(cls, id):
        """Obtiene una categoría por ID"""
        return cls.collection.find_one({"_id": ObjectId(id)})
    
    @classmethod
    def find_by_slug(cls, slug):
        """Obtiene una categoría por slug"""
        return cls.collection.find_one({"slug": slug})
    
    @classmethod
    def create(cls, data):
        """Crea una nueva categoría"""
        data['fecha_creacion'] = datetime.utcnow()
        data['fecha_actualizacion'] = datetime.utcnow()
        result = cls.collection.insert_one(data)
        return str(result.inserted_id)
    
    @classmethod
    def update(cls, id, data):
        """Actualiza una categoría"""
        data['fecha_actualizacion'] = datetime.utcnow()
        result = cls.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": data}
        )
        return result.modified_count > 0
    
    @classmethod
    def delete(cls, id):
        """Elimina una categoría"""
        result = cls.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0


class Platillo:
    collection = db["platillos"]
    
    # Mapeo de categorías a nombres
    NOMBRE_CATEGORIAS = {
        'entrada': 'Entrada',
        'plato_fuerte': 'Plato Fuerte',
        'bebida': 'Bebida',
        'postre': 'Postre',
        'especial': 'Especial'
    }
    
    @classmethod
    def find_all(cls, filtro=None):
        """Obtiene todos los platillos con filtros opcionales"""
        query = filtro or {}
        platillos = list(cls.collection.find(query).sort('nombre', 1))
        
        # Agregar nombre de categoría a cada platillo
        for platillo in platillos:
            platillo['categoria_nombre'] = cls.NOMBRE_CATEGORIAS.get(
                platillo.get('categoria', ''), 
                platillo.get('categoria', '')
            )
        
        return platillos
    
    @classmethod
    def find_by_id(cls, id):
        """Obtiene un platillo por ID"""
        platillo = cls.collection.find_one({"_id": ObjectId(id)})
        if platillo:
            platillo['categoria_nombre'] = cls.NOMBRE_CATEGORIAS.get(
                platillo.get('categoria', ''), 
                platillo.get('categoria', '')
            )
        return platillo
    
    @classmethod
    def find_by_categoria(cls, categoria):
        """Obtiene platillos por categoría"""
        platillos = list(cls.collection.find({"categoria": categoria}).sort('nombre', 1))
        
        for platillo in platillos:
            platillo['categoria_nombre'] = cls.NOMBRE_CATEGORIAS.get(
                platillo.get('categoria', ''), 
                platillo.get('categoria', '')
            )
        
        return platillos
    
    @classmethod
    def find_disponibles(cls):
        """Obtiene solo platillos disponibles"""
        campos = {"nombre": 1, "descripcion": 1, "categoria": 1, "precio": 1, "imagen": 1, "disponible": 1}
        platillos = list(cls.collection.find({"disponible": True}, campos).sort('nombre', 1))
        
        for platillo in platillos:
            platillo['categoria_nombre'] = cls.NOMBRE_CATEGORIAS.get(
                platillo.get('categoria', ''), 
                platillo.get('categoria', '')
            )
        
        return platillos
    
    @classmethod
    def create(cls, data):
        """Crea un nuevo platillo"""
        from datetime import datetime
        
        platillo = {
            'nombre': data.get('nombre'),
            'descripcion': data.get('descripcion', ''),
            'categoria': data.get('categoria', 'plato_fuerte'),
            'precio': float(data.get('precio', 0)),
            'imagen': data.get('imagen', data.get('imagen_url', '')),
            'disponible': data.get('disponible', True),
            'tiempo_preparacion': data.get('tiempo_preparacion', 15),
            'nivel_picante': int(data.get('nivel_picante', 0)),
            'alergenos': data.get('alergenos', []),
            'notas': data.get('notas', ''),
            'fecha_creacion': datetime.utcnow(),
            'fecha_actualizacion': datetime.utcnow()
        }
        
        result = cls.collection.insert_one(platillo)
        return str(result.inserted_id)
    
    @classmethod
    def update(cls, id, data):
        """Actualiza un platillo"""
        from datetime import datetime
        
        update_data = {
            'fecha_actualizacion': datetime.utcnow()
        }
        
        # Solo actualizar campos que se proporcionan
        if 'nombre' in data:
            update_data['nombre'] = data['nombre']
        if 'descripcion' in data:
            update_data['descripcion'] = data['descripcion']
        if 'categoria' in data:
            update_data['categoria'] = data['categoria']
        if 'precio' in data:
            update_data['precio'] = float(data['precio'])
        if 'imagen' in data:
            update_data['imagen'] = data['imagen']
        if 'imagen_url' in data:
            update_data['imagen'] = data['imagen_url']
        if 'disponible' in data:
            update_data['disponible'] = data['disponible']
        if 'tiempo_preparacion' in data:
            update_data['tiempo_preparacion'] = data['tiempo_preparacion']
        if 'nivel_picante' in data:
            update_data['nivel_picante'] = data['nivel_picante']
        if 'alergenos' in data:
            update_data['alergenos'] = data['alergenos']
        if 'notas' in data:
            update_data['notas'] = data['notas']
        
        result = cls.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    @classmethod
    def delete(cls, id):
        """Elimina un platillo"""
        result = cls.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
    
    @classmethod
    def buscar(cls, termino, solo_disponibles=True):
        """Busca platillos por nombre o descripción"""
        query = {
            "$or": [
                {"nombre": {"$regex": termino, "$options": "i"}},
                {"descripcion": {"$regex": termino, "$options": "i"}}
            ]
        }
        if solo_disponibles:
            query["disponible"] = True
        platillos = list(cls.collection.find(query).sort('nombre', 1))
        
        for platillo in platillos:
            platillo['categoria_nombre'] = cls.NOMBRE_CATEGORIAS.get(
                platillo.get('categoria', ''), 
                platillo.get('categoria', '')
            )
        
        return platillos
    
    @classmethod
    def toggle_disponible(cls, id):
        """Cambia la disponibilidad de un platillo"""
        platillo = cls.find_by_id(id)
        if platillo:
            nuevo_estado = not platillo.get('disponible', True)
            result = cls.collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": {"disponible": nuevo_estado, "fecha_actualizacion": datetime.utcnow()}}
            )
            return result.modified_count > 0
        return False


class Receta:
    collection = db["recetas"]
    
    @classmethod
    def find_by_platillo(cls, platillo_id):
        """Obtiene la receta de un platillo"""
        return cls.collection.find_one({"platillo_id": platillo_id})
    
    @classmethod
    def create(cls, data):
        """Crea una nueva receta"""
        data['fecha_creacion'] = datetime.utcnow()
        data['fecha_actualizacion'] = datetime.utcnow()
        result = cls.collection.insert_one(data)
        return str(result.inserted_id)
    
    @classmethod
    def update(cls, platillo_id, data):
        """Actualiza una receta"""
        data['fecha_actualizacion'] = datetime.utcnow()
        result = cls.collection.update_one(
            {"platillo_id": platillo_id},
            {"$set": data},
            upsert=True
        )
        return True
    
    @classmethod
    def delete(cls, platillo_id):
        """Elimina una receta"""
        result = cls.collection.delete_one({"platillo_id": platillo_id})
        return result.deleted_count > 0
