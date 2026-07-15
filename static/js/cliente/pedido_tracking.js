/**
 * ============================================
 * TRACKING DE PEDIDO - Callejón 9
 * Escucha la sala Socket.IO 'cliente_{id}' (emitida por
 * controllers/api/v1/pedido_movil_controller.py) y hace
 * polling de respaldo por si el socket se desconecta.
 * ============================================
 */

const PedidoTracking = (function () {
    let socket = null;
    let pollingInterval = null;

    const ESTADO_INFO = {
        pendiente:  { label: 'Recibido',        paso: 1, icon: 'bi-receipt' },
        recibido:   { label: 'Recibido',        paso: 1, icon: 'bi-receipt' },
        en_cocina:  { label: 'En preparación',  paso: 2, icon: 'bi-egg-fried' },
        listo:      { label: 'Listo',           paso: 3, icon: 'bi-check-circle' },
        entregado:  { label: 'Entregado',       paso: 4, icon: 'bi-bag-check' },
        cancelado:  { label: 'Cancelado',       paso: 0, icon: 'bi-x-circle' },
    };

    function getEstadoInfo(estado) {
        return ESTADO_INFO[estado] || { label: estado, paso: 1, icon: 'bi-question-circle' };
    }

    /**
     * Conecta el socket y se une a la sala del cliente para recibir
     * 'pedido_actualizado' en tiempo real. Requiere el id del cliente
     * (se obtiene de /api/v1/clientes/perfil).
     */
    function conectar(clienteId, onActualizacion) {
        if (socket) return;

        socket = io(window.location.origin, {
            transports: ['polling', 'websocket'],
            timeout: 10000
        });

        socket.on('connect', () => {
            socket.emit('join_room', `cliente_${clienteId}`);
        });

        socket.on('pedido_actualizado', (data) => {
            onActualizacion(data);
        });
    }

    function iniciarPolling(callback, intervaloMs = 15000) {
        detenerPolling();
        pollingInterval = setInterval(callback, intervaloMs);
    }

    function detenerPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    }

    function desconectar() {
        detenerPolling();
        if (socket) {
            socket.disconnect();
            socket = null;
        }
    }

    return { conectar, iniciarPolling, detenerPolling, desconectar, getEstadoInfo };
})();
