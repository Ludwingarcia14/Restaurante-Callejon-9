# cqrs/queries/ia/models/analyze_doc_query.py

from werkzeug.datastructures import FileStorage

class AnalyzeDocumentQuery:
    """DTO para encapsular el archivo subido y la información de la ruta."""
    
    def __init__(self, uploaded_file: FileStorage, upload_folder: str):
        self.uploaded_file = uploaded_file
        self.upload_folder = upload_folder
        self.file_path = None # Se inicializa en None y se asigna en el Handler