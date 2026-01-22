from config.db import db
from bson.objectid import ObjectId
from datetime import datetime

class DocumentoFisica:
    collection = db["documentofisica"]

    def __init__(self, data):
        """
        Constructor que mapea el JSON de la BD a atributos del objeto
        para que el Dashboard pueda leerlos (ej: doc.ine).
        """
        self.raw_data = data
        self.docs = data.get('documentos', {})

        # --- MAPEO DE RUTAS PARA EL DASHBOARD ---
        # Busca dentro de 'documentos' -> 'campo_especifico' -> 'ruta'
        self.ine = self._get_ruta('ine_fisica')
        self.domicilio = self._get_ruta('domicilio_fisica')
        self.situacion_fiscal = self._get_ruta('situacion_fiscal_fisica')
        self.buro_credito = self._get_ruta('buro_credito_fisica')
        self.estados_cuenta = self._get_ruta('estados_cuenta_fisica')
        self.declaracion_anual = self._get_ruta('declaracion_anual_fisica')
        self.estados_financieros = self._get_ruta('estados_financieros_fisica')

    def _get_ruta(self, key):
        """Método auxiliar para extraer la ruta de forma segura."""
        doc = self.docs.get(key)
        
        # CASO LISTA (Estados de Cuenta): Retornamos lista de rutas
        if isinstance(doc, list):
            return [d.get('ruta') for d in doc if isinstance(d, dict) and d.get('ruta')]
            
        # CASO DICCIONARIO (Resto de docs): Retornamos string
        if isinstance(doc, dict) and doc.get('ruta'):
            return doc.get('ruta')
            
        return None

    # ==========================================
    # MÉTODOS NUEVOS (PARA DASHBOARD)
    # ==========================================
    @classmethod
    def get_by_user_id(cls, user_id):
        """
        Busca el documento por usuario_id y devuelve una instancia de DocumentoFisica.
        """
        try:
            # Intentar buscar por string y ObjectId para robustez
            query = {"usuario_id": str(user_id)}
            data = cls.collection.find_one(query)
            
            if not data:
                try:
                    query = {"usuario_id": ObjectId(user_id)}
                    data = cls.collection.find_one(query)
                except:
                    pass

            if data:
                return cls(data) # Retorna el objeto inicializado
            return None
        except Exception as e:
            print(f"Error en DocumentoFisica.get_by_user_id: {e}")
            return None

    # ==========================================
    # TUS MÉTODOS EXISTENTES (MANTENIDOS)
    # ==========================================
    @staticmethod
    def insertar(data):
        return DocumentoFisica.collection.insert_one(data)

    @staticmethod
    def obtener_todos():
        return list(DocumentoFisica.collection.find())
    
    @staticmethod
    def update_document_analysis(usuario_id: ObjectId, document_type: str, analysis_data: dict):
        target_field = "domicilio_fisica" 
        set_operations = {}
        base_path = f"documentos.{target_field}.analisis"
        
        for key, value in analysis_data.items():
            clean_key = key.replace("comprobante_domicilio_", "")
            if clean_key == "domicilio_extraido":
                clean_key = "direccion_extraida"
            set_operations[f"{base_path}.{clean_key}"] = value

        set_operations[f"{base_path}.fecha_analisis"] = datetime.utcnow()

        result = DocumentoFisica.collection.update_one(
            {"usuario_id": usuario_id},
            {"$set": set_operations}
        )
        return result.modified_count > 0