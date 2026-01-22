from config.db import db
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.datastructures import FileStorage
from typing import Dict, Any, Union
import uuid
import os
from flask import current_app

class UpdateProfileCommand:
    def __init__(self, usuario_id: str, form_data: Dict[str, str], file_data: Dict[str, FileStorage]):
        self.usuario_id = usuario_id
        self.usuario_obj_id = ObjectId(usuario_id)
        self.form_data = form_data
        self.file_data = file_data

    def execute(self):
        """
        Actualiza el perfil del cliente (usuarios y documentos asociados).
        """
        # 1. Datos a actualizar en la colección 'usuarios'
        update_data = {
            "usuario_nombre": self.form_data.get("usuario_nombre"),
            "usuario_apellidos": self.form_data.get("usuario_apellidos"),
            "usuario_telefono": self.form_data.get("usuario_telefono"),
            "usuario_email": self.form_data.get("usuario_email")
        }
        
        # 2. Subida de foto de perfil (opcional)
        foto = self.file_data.get("usuario_foto")
        if foto and foto.filename != "":
            foto_path = f"static/uploads/{uuid.uuid4()}_{foto.filename}"
            # Asegúrate de que el path de guardado sea correcto
            full_path = os.path.join(current_app.root_path, foto_path)
            foto.save(full_path)
            update_data["usuario_foto"] = foto_path

        # 3. Actualizar datos en la colección 'usuarios'
        db.usuarios.update_one({"_id": self.usuario_obj_id}, {"$set": update_data})

        # 4. Subida de documentos adicionales
        for key in ("doc_ine", "doc_domicilio", "doc_ingresos"):
            archivo = self.file_data.get(key)
            if archivo and archivo.filename != "":
                save_path = f"static/uploads/{uuid.uuid4()}_{archivo.filename}"
                full_save_path = os.path.join(current_app.root_path, save_path)
                
                archivo.save(full_save_path)
                
                # Insertar registro de documento en la colección 'docs'
                db.docs.insert_one({
                    "user_id": self.usuario_id,
                    "tipo": key,
                    "path": save_path,
                    "fecha": datetime.utcnow()
                })