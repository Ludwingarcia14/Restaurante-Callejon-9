from flask import request, jsonify
from datetime import datetime
from models.Pedido import db, Pedido
from models.DetallePedido import DetallePedido
from models.Platillo import Platillo
from models.PlatilloNoDisponible import PlatilloNoDisponible

class PedidosController:
    
    @staticmethod
    def obtener_todos_pedidos():
        """Obtiene todos los pedidos en estado pendiente"""
        pedidos = Pedido.query.filter_by(estado='pendiente').all()
        return [PedidosController._serializar_pedido(p) for p in pedidos]
    
    @staticmethod
    def obtener_pedidos_preparacion():
        """Obtiene todos los pedidos en preparación"""
        pedidos = Pedido.query.filter_by(estado='preparacion').all()
        return [PedidosController._serializar_pedido(p) for p in pedidos]
    
    @staticmethod
    def obtener_pedidos_listos():
        """Obtiene todos los pedidos listos para entregar"""
        pedidos = Pedido.query.filter_by(estado='listo').all()
        return [PedidosController._serializar_pedido(p) for p in pedidos]
    
    @staticmethod
    def crear_pedido(data):
        """Crea un nuevo pedido"""
        try:
            nuevo_pedido = Pedido(
                numero_pedido=data.get('numero_pedido'),
                numero_mesa=data.get('numero_mesa'),
                usuario_registro=data.get('usuario_registro'),
                estado='pendiente'
            )
            db.session.add(nuevo_pedido)
            db.session.commit()
            return {'success': True, 'pedido_id': nuevo_pedido.id}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def obtener_detalle_pedido(pedido_id):
        """Obtiene los detalles de un pedido específico"""
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            return None
        return {
            'pedido_id': pedido.id,
            'numero_pedido': pedido.numero_pedido,
            'numero_mesa': pedido.numero_mesa,
            'hora_entrada': pedido.hora_entrada.strftime('%H:%M'),
            'minutos_esperando': pedido.minutos_esperando(),
            'usuario_registro': pedido.usuario_registro,
            'total_cuenta': pedido.total_cuenta,
            'detalles': [
                {
                    'id': d.id,
                    'platillo': d.platillo.nombre,
                    'cantidad': d.cantidad,
                    'notas_especiales': d.notas_especiales,
                    'estado_preparacion': d.estado_preparacion,
                    'precio': d.platillo.precio
                }
                for d in pedido.detalles
            ]
        }
    
    @staticmethod
    def agregar_platillo_pedido(pedido_id, data):
        """Agrega un platillo a un pedido"""
        try:
            detalle = DetallePedido(
                pedido_id=pedido_id,
                platillo_id=data.get('platillo_id'),
                cantidad=data.get('cantidad', 1),
                notas_especiales=data.get('notas_especiales')
            )
            db.session.add(detalle)
            db.session.commit()
            return {'success': True, 'detalle_id': detalle.id}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def iniciar_preparacion(pedido_id):
        """Cambia el estado del pedido a preparación"""
        try:
            pedido = Pedido.query.get(pedido_id)
            pedido.estado = 'preparacion'
            db.session.commit()
            return {'success': True}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def actualizar_estado_platillo(detalle_id, nuevo_estado):
        """Actualiza el estado de un platillo (no_iniciado, preparando, listo)"""
        try:
            detalle = DetallePedido.query.get(detalle_id)
            detalle.estado_preparacion = nuevo_estado
            db.session.commit()
            return {'success': True}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def marcar_pedido_listo(pedido_id):
        """Marca un pedido como listo para entregar"""
        try:
            pedido = Pedido.query.get(pedido_id)
            pedido.estado = 'listo'
            db.session.commit()
            return {'success': True}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _serializar_pedido(pedido):
        """Serializa un objeto Pedido a diccionario"""
        return {
            'id': pedido.id,
            'numero_pedido': pedido.numero_pedido,
            'numero_mesa': pedido.numero_mesa,
            'hora_entrada': pedido.hora_entrada.strftime('%H:%M'),
            'minutos_esperando': pedido.minutos_esperando(),
            'usuario_registro': pedido.usuario_registro,
            'estado': pedido.estado,
            'total_cuenta': pedido.total_cuenta
        }