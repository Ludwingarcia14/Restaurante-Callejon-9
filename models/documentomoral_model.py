from config.db import db
from bson.objectid import ObjectId

class DocumentoMoral:
    collection = db["documentomoral"]

    def __init__(self, data):
        """Constructor para mapeo de datos."""
        self.raw_data = data
        self.docs = data.get('documentos', {})

        # --- MAPEO DE RUTAS MORAL ---
        self.ine = self._get_ruta('ine_moral')
        self.domicilio = self._get_ruta('domicilio_moral')
        self.situacion_fiscal = self._get_ruta('situacion_fiscal_moral')
        self.buro_credito = self._get_ruta('buro_credito_moral')
        self.acta_constitutiva = self._get_ruta('acta_constitutiva_moral')
        self.poderes = self._get_ruta('poderes_notariales_moral')
        self.declaracion_anual = self._get_ruta('declaracion_anual_moral')
        self.estados_financieros = self._get_ruta('estados_financieros_moral')
        self.estados_cuenta = self._get_ruta('estados_cuenta_moral')

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
        try:
            query = {"usuario_id": str(user_id)}
            data = cls.collection.find_one(query)
            
            if not data:
                try:
                    query = {"usuario_id": ObjectId(user_id)}
                    data = cls.collection.find_one(query)
                except:
                    pass

            if data:
                return cls(data)
            return None
        except Exception as e:
            print(f"Error en DocumentoMoral.get_by_user_id: {e}")
            return None

    # ==========================================
    # TUS MÉTODOS EXISTENTES
    # ==========================================
    @staticmethod
    def insertar(data):
        return DocumentoMoral.collection.insert_one(data)

    @staticmethod
    def obtener_todos():
        return list(DocumentoMoral.collection.find())