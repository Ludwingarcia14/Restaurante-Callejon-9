"""
Controlador de Menú
Administra platillos, categorías y recetas del menú
"""
from flask import render_template, session, redirect, url_for, request, jsonify
from models.menu_model import Platillo, Categoria, Receta
from bson.objectid import ObjectId
import json
import logging

logger = logging.getLogger(__name__)

class MenuController:
    # ============================================
    # VISTAS DE PLATILLOS
    # ============================================
    
    @staticmethod
    def index():
        """Lista todos los platillos del menú"""
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))
        
        platillos = Platillo.find_all()
        return render_template("admin/menu/lista.html", platillos=platillos)
    
    @staticmethod
    def crear():
        """Muestra el formulario para crear un platillo"""
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))
        
        return render_template("admin/menu/crear.html")
    
    @staticmethod
    def editar(platillo_id):
        """Muestra el formulario para editar un platillo"""
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))
        
        platillo = Platillo.find_by_id(platillo_id)
        if not platillo:
            return redirect(url_for("routes.admin_menu"))
        
        return render_template("admin/menu/editar.html", platillo=platillo)
    
    @staticmethod
    def detalle(platillo_id):
        """Muestra los detalles de un platillo"""
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))
        
        platillo = Platillo.find_by_id(platillo_id)
        if not platillo:
            return redirect(url_for("routes.admin_menu"))
        
        return render_template("admin/menu/detalle.html", platillo=platillo)
    
    # ============================================
    # VISTAS DE CATEGORÍAS
    # ============================================
    
    @staticmethod
    def categorias():
        """Lista todas las categorías"""
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))
        
        categorias = Categoria.find_all()
        return render_template("admin/menu/categorias.html", categorias=categorias)
    
    @staticmethod
    def crear_categoria():
        """Muestra el formulario para crear una categoría"""
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))
        
        return render_template("admin/menu/crear_categoria.html")
    
    @staticmethod
    def editar_categoria(categoria_id):
        """Muestra el formulario para editar una categoría"""
        if "usuario_id" not in session:
            return redirect(url_for("routes.login"))
        
        categoria = Categoria.find_by_id(categoria_id)
        if not categoria:
            return redirect(url_for("routes.admin_menu_categorias"))
        
        return render_template("admin/menu/editar_categoria.html", categoria=categoria)
    
    # ============================================
    # API: PLATILLOS
    # ============================================
    
    @staticmethod
    def api_crear_platillo():
        """API: Crea un nuevo platillo"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            data = request.form.to_dict()
            
            # Procesar alergenos si viene como string
            if 'alergenos' in data and isinstance(data['alergenos'], str):
                data['alergenos'] = json.loads(data['alergenos'])
            
            platillo_id = Platillo.create(data)
            
            return jsonify({
                "success": True,
                "message": "Platillo creado correctamente",
                "platillo_id": platillo_id
            })
        except Exception as e:
            logger.error(f"Error en api_actualizar_categoria: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_actualizar_platillo(platillo_id):
        """API: Actualiza un platillo"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            data = request.form.to_dict()
            
            # Procesar alergenos si viene como string
            if 'alergenos' in data and isinstance(data['alergenos'], str):
                data['alergenos'] = json.loads(data['alergenos'])
            
            # Convertir disponible a booleano
            if 'disponible' in data:
                data['disponible'] = data['disponible'] == 'on' or data['disponible'] == True
            
            # Convertir nivel_picante a entero
            if 'nivel_picante' in data:
                data['nivel_picante'] = int(data['nivel_picante'])
            
            # Convertir tiempo_preparacion a entero
            if 'tiempo_preparacion' in data:
                data['tiempo_preparacion'] = int(data['tiempo_preparacion'])
            
            success = Platillo.update(platillo_id, data)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Platillo actualizado correctamente"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "No se pudo actualizar el platillo"
                }), 400
        except Exception as e:
            logger.error(f"Error en api_actualizar_platillo: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_eliminar_platillo(platillo_id):
        """API: Elimina un platillo"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            success = Platillo.delete(platillo_id)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Platillo eliminado correctamente"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "No se pudo eliminar el platillo"
                }), 400
        except Exception as e:
            logger.error(f"Error en api_eliminar_platillo: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_buscar_platillos():
        """API: Busca platillos"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            termino = request.args.get('q', '')
            platillos = Platillo.buscar(termino)
            
            return jsonify({
                "success": True,
                "platillos": platillos
            })
        except Exception as e:
            logger.error(f"Error en api_crear_categoria: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_get_platillo(platillo_id):
        """API: Obtiene un platillo por ID"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            platillo = Platillo.find_by_id(platillo_id)
            
            if platillo:
                return jsonify({
                    "success": True,
                    "platillo": platillo
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "Platillo no encontrado"
                }), 404
        except Exception as e:
            logger.error(f"Error en api_get_platillo: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_get_menu():
        """API: Obtiene el menú completo (para meseros/cocina)"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            platillos = Platillo.find_disponibles()
            
            return jsonify({
                "success": True,
                "platillos": platillos
            })
        except Exception as e:
            logger.error(f"Error en api_get_menu: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_toggle_platillo(platillo_id):
        """API: Cambia la disponibilidad de un platillo"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            success = Platillo.toggle_disponible(platillo_id)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Disponibilidad actualizada"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "No se pudo actualizar"
                }), 400
        except Exception as e:
            logger.error(f"Error en api_toggle_platillo: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    # ============================================
    # API: CATEGORÍAS
    # ============================================
    
    @staticmethod
    def api_crear_categoria():
        """API: Crea una nueva categoría"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            data = request.get_json()
            categoria_id = Categoria.create(data)
            
            return jsonify({
                "success": True,
                "message": "Categoría creada correctamente",
                "categoria_id": categoria_id
            })
        except Exception as e:
            logger.error(f"Error en api_crear_categoria: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_actualizar_categoria(categoria_id):
        """API: Actualiza una categoría"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            data = request.get_json()
            success = Categoria.update(categoria_id, data)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Categoría actualizada correctamente"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "No se pudo actualizar la categoría"
                }), 400
        except Exception as e:
            logger.error(f"Error en api_actualizar_categoria: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_eliminar_categoria(categoria_id):
        """API: Elimina una categoría"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            success = Categoria.delete(categoria_id)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Categoría eliminada correctamente"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "No se pudo eliminar la categoría"
                }), 400
        except Exception as e:
            logger.error(f"Error en api_eliminar_categoria: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
    
    @staticmethod
    def api_get_categorias():
        """API: Obtiene todas las categorías"""
        if "usuario_id" not in session:
            return jsonify({"success": False, "message": "No autorizado"}), 401
        
        try:
            categorias = Categoria.find_all()
            
            return jsonify({
                "success": True,
                "categorias": categorias
            })
        except Exception as e:
            logger.error(f"Error en api_get_categorias: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error interno del servidor"
            }), 500
