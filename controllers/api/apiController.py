from bson import ObjectId
from flask import jsonify, session, Flask, request
from config.db import db
import os
import datetime
from dotenv import load_dotenv

# Nota: request, time, jwt, requests ya no se importan aquí porque están
# en los Handlers (salvo que los necesites para otras funciones del controller).
# Los dejé solo si son necesarios para las funciones de Flask/sesión.
import requests # Necesario si vas a usarlo en el controller para otra cosa, sino, al handler
import jwt # Necesario si vas a usarlo en el controller para otra cosa, sino, al handler
import time # Necesario si vas a usarlo en el controller para otra cosa, sino, al handler

from models.landing_model import LandingManager, PageManager
from models.notificacion import Notificacion

load_dotenv()

# ===================================================================
# 🚨 DELEGACIÓN CQRS 🚨
# Importamos los Handlers y Models desde la carpeta 'cqrs'
# ===================================================================

# Handlers de Consultas (Queries)
from cqrs.queryes.handlers.geo_handler import GeoQueryHandler
from cqrs.queryes.handlers.widget_handler import WidgetQueryHandler
from cqrs.queryes.handlers.usuario_handler import UsuarioQueryHandler
from cqrs.queryes.handlers.notificacion_query_handler import NotificacionQueryHandler

# Handlers de Comandos (Commands)
from cqrs.commands.handlers.notificacion_handler import NotificacionCommandHandler
from cqrs.commands.handlers.notificacion_leida_handler import MarcarLeidasCommandHandler

# Modelos de Comandos (DTOs)
from cqrs.commands.models.notificar_command import NotificarUsuarioCommand

# ===================================================================

app = Flask(__name__)
app.config['SOCKET_JWT_SECRET'] = os.environ.get('SOCKET_JWT_SECRET')

# Instanciación e Inyección de Dependencias
# Los Handlers se crean una sola vez
geo_handler = GeoQueryHandler(db)
widget_handler = WidgetQueryHandler() 
usuario_handler = UsuarioQueryHandler(db, app.config) 


class apiController:

    # ------------------------------------------------------------------
    # 1. GEOGRAFÍA (QUERIES DE LECTURA) - Toda la lógica en geo_handler.py
    # ------------------------------------------------------------------
    
    @staticmethod
    def extract_estados():
        if "usuario_id" not in session: return jsonify({"error": "No autorizado"}), 401
        return jsonify(geo_handler.get_estados()) # 👈 Delegación
    
    @staticmethod
    def extract_municipios(estado_id):
        if "usuario_id" not in session: return jsonify({"error": "No autorizado"}), 401
        return jsonify(geo_handler.get_municipios(estado_id)) # 👈 Delegación

    @staticmethod
    def extract_colonias(municipio_id):
        if "usuario_id" not in session: return jsonify({"error": "No autorizado"}), 401
        return jsonify(geo_handler.get_colonias(municipio_id)) # 👈 Delegación

    @staticmethod
    def extract_cp(cp):
        if "usuario_id" not in session: return jsonify({"error": "No autorizado"}), 401
        result = geo_handler.get_cp_data(cp) # 👈 Delegación
        if not result: return jsonify({"error": "CP no encontrado"}), 404
        return jsonify(result)

    # ------------------------------------------------------------------
    # 2. WIDGETS (QUERIES DE LECTURA CON CACHÉ) - Toda la lógica en widget_handler.py
    # ------------------------------------------------------------------

    @staticmethod
    def get_divisas_data():
        if "usuario_id" not in session: return jsonify({"error": "No autorizado"}), 401
        return jsonify(widget_handler.get_divisas_data()) # 👈 Delegación

    @staticmethod
    def get_bolsa_data():
        if "usuario_id" not in session: return jsonify({"error": "No autorizado"}), 401
        return jsonify(widget_handler.get_bolsa_data()) # 👈 Delegación
        
    # ------------------------------------------------------------------
    # 3. USUARIO / TOKEN (QUERY) - Toda la lógica en usuario_handler.py
    # ------------------------------------------------------------------
    
    @staticmethod
    def get_my_data():
        if 'usuario_id' not in session: return jsonify({'error': 'No autenticado'}), 401
        
        try:
            # Llama al handler para validar rol, buscar en BD y generar el token JWT
            result = usuario_handler.get_user_data_and_token(
                user_id_str=session['usuario_id'], 
                session_data=session
            ) # 👈 Delegación
            return jsonify(result)
        except Exception as e:
            print(f"Error generando token en controller: {e}")
            return jsonify({'error': f'Error al generar token: {str(e)}'}), 500

    # ------------------------------------------------------------------
    # 4. NOTIFICACIONES (COMMANDS Y QUERIES)
    # ------------------------------------------------------------------
    
    @staticmethod 
    def notificar_usuario(id_usuario):
        if "usuario_id" not in session: return jsonify({"error": "No autorizado"}), 401
        
        body = request.json
        mensaje = body.get("mensaje")
        tipo = body.get("tipo", "general")

        if not mensaje: return jsonify({"error": "Mensaje requerido"}), 400

        # 1. Crear el objeto Command (DTO)
        command = NotificarUsuarioCommand(id_usuario=id_usuario, mensaje=mensaje, tipo=tipo)
        
        # 2. Ejecutar el Command Handler (Write Logic)
        try:
            # El handler es responsable de Guardar en BD y Enviar por Socket
            result = NotificacionCommandHandler.handle(command, Notificacion) 
            return jsonify(result)
        except Exception as e:
            print(f"Error al ejecutar comando notificar_usuario: {e}")
            return jsonify({"ok": False, "msg": f"Error interno al procesar: {e}"}), 500
    
    @staticmethod
    def obtener_notificaciones(id_usuario):
        if "usuario_id" not in session: return jsonify({"error": "No autorizado"}), 401
        
        # Ejecutar el Query Handler (Read Logic)
        try:
            data = NotificacionQueryHandler.get_notificaciones(id_usuario, Notificacion)
            return jsonify(data)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": f"Error al obtener notificaciones: {e}"}), 500
    
    @staticmethod
    def marcar_leidas(id_usuario):
        if "usuario_id" not in session: return jsonify({"error": "No autorizado"}), 401

        # Ejecutar el Command Handler (Write Logic)
        try:
            result = MarcarLeidasCommandHandler.handle(id_usuario, Notificacion)
            return jsonify(result)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"ok": False, "msg": f"Error al marcar leídas: {e}"}), 500
        
    @staticmethod
    def get_carusel_items():
        try:
            carousel_items = db.carousel.find().sort("fecha_creacion", -1)

            items_list = []
            for item in carousel_items:
                item["_id"] = str(item["_id"])
                items_list.append(item)

            return jsonify({
                "success": True,
                "data": items_list
            }), 200

        except Exception as e:
            print(f"Error al obtener items del carrusel: {e}")
            return jsonify({
                "success": False,
                "error": "Error interno al obtener items del carrusel"
            }), 500
        
    @staticmethod
    def get_content_by_slug(tipo, slug):
        """
        Busca el contenido dinámico diseñado.
        Ejemplo de ruta: /api/v1/content/expo/gran-evento-2026
        """
        target_link = f"/landing/{tipo}/{slug}"
        # Buscamos en la colección el registro que coincida con ese link
        content = LandingManager.collection.find_one({"btn_link": target_link})
        
        if content:
            content["_id"] = str(content["_id"])
            return jsonify(content), 200
        
        return jsonify({"error": "Contenido no encontrado"}), 404

    @staticmethod
    def get_page_content(tipo, slug):
        """
        Ruta pública API: /api/public/content/<tipo>/<slug>
        Ejemplo: /api/public/content/expo/feria-emprendedores-2026
        """
        try:
            # Buscamos por slug y tipo (ej: 'expo', 'mi-evento')
            page = PageManager.get_page_by_slug(tipo, slug)
            
            if not page:
                return jsonify({
                    "success": False, 
                    "message": "Página no encontrada o inactiva"
                }), 404
            
            # Devolvemos la data para que Laravel la renderice
            return jsonify({
                "success": True, 
                "data": page 
            }), 200

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500