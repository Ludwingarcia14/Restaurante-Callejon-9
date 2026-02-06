from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)

# Datos para el carrusel
CARRUSEL_DATA = [
    {
        'id': 1,
        'titulo': 'Misión',
        'descripcion': 'Ofrecer una experiencia gastronómica excepcional combinando ingredientes locales de la más alta calidad con técnicas culinarias innovadoras, creando momentos memorables para nuestros comensales.'
    },
    {
        'id': 2,
        'titulo': 'Visión',
        'descripcion': 'Ser reconocidos como el restaurante de referencia en la ciudad, distinguidos por nuestra autenticidad, calidad y compromiso con la sostenibilidad y la comunidad local.'
    },
    {
        'id': 3,
        'titulo': 'Objetivo',
        'descripcion': 'Superar las expectativas de cada cliente a través de un servicio excepcional, platos creativos y un ambiente acogedor que invite a nuestros visitantes a regresar una y otra vez.'
    },
    {
        'id': 4,
        'titulo': 'Valores',
        'descripcion': 'Calidad, autenticidad, sostenibilidad, innovación y hospitalidad. Estos pilares guían cada decisión que tomamos, desde la selección de ingredientes hasta la atención al cliente.'
    },
    {
        'id': 5,
        'titulo': 'Meta',
        'descripcion': 'Expandir nuestra propuesta gastronómica manteniendo la esencia que nos define, creando nuevos espacios donde más personas puedan disfrutar de la experiencia Callejón 19.'
    }
]

@app.route('/')
def index():
    """Ruta principal de la aplicación"""
    año_actual = datetime.now().year
    return render_template('index.html', 
                         carrusel_data=CARRUSEL_DATA,
                         año_actual=año_actual)

@app.route('/api/carrusel', methods=['GET'])
def get_carrusel():
    """API para obtener datos del carrusel"""
    return jsonify(CARRUSEL_DATA)

@app.route('/reservar', methods=['POST'])
def hacer_reserva():
    """Procesar reservas"""
    try:
        data = request.form
        
        # Aquí normalmente guardarías en una base de datos
        reserva = {
            'nombre': data.get('nombre'),
            'email': data.get('email'),
            'telefono': data.get('telefono'),
            'fecha': data.get('fecha'),
            'hora': data.get('hora'),
            'personas': data.get('personas'),
            'fecha_reserva': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Simulación de guardado exitoso
        print(f"Reserva recibida: {reserva}")
        
        return jsonify({
            'success': True,
            'message': '¡Reserva realizada con éxito! Te contactaremos pronto para confirmar.',
            'reserva': reserva
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al procesar la reserva: {str(e)}'
        }), 400

@app.route('/newsletter', methods=['POST'])
def suscribir_newsletter():
    """Procesar suscripción al newsletter"""
    try:
        email = request.form.get('email')
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Por favor, proporciona un email válido'
            }), 400
        
        # Aquí normalmente guardarías en una base de datos
        print(f"Nuevo suscriptor al newsletter: {email}")
        
        return jsonify({
            'success': True,
            'message': f'¡Gracias por suscribirte con el correo: {email}!'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al procesar la suscripción: {str(e)}'
        }), 400

if __name__ == '__main__':
    print("=" * 60)
    print("SERVIDOR CALLEJÓN 19 - WIX")
    print("Iniciando en: http://127.0.0.1:5000")
    print("=" * 60)
    
    app.run(debug=True, port=5000)