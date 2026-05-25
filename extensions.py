# extensions.py — instancias compartidas, se inicializan en app.py via init_app()
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

socketio = SocketIO()
limiter = Limiter(key_func=get_remote_address)
