/**
 * ============================================
 * GEOLOCALIZACIÓN DEL CLIENTE - Callejón 9
 * Lectura puntual de GPS (no tracking continuo).
 * El tracking continuo es exclusivo del repartidor
 * (ver static/js/repartidor/*.js y models/sensor_model.py).
 * ============================================
 */

const Geolocalizacion = (function () {

    /**
     * Pide al navegador la posición actual una sola vez.
     * Devuelve una Promise<{lat, lng, accuracy}>.
     */
    function obtenerUbicacionActual(opciones = {}) {
        return new Promise((resolve, reject) => {
            if (!('geolocation' in navigator)) {
                reject(new Error('Tu navegador no soporta geolocalización'));
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve({
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    });
                },
                (error) => {
                    let mensaje = 'No se pudo obtener tu ubicación';
                    if (error.code === error.PERMISSION_DENIED || error.code === 1) {
                        mensaje = 'Permiso de ubicación denegado. Puedes escribir tu dirección manualmente.';
                    } else if (error.code === error.TIMEOUT || error.code === 3) {
                        mensaje = 'Tardó demasiado en obtener tu ubicación. Inténtalo de nuevo.';
                    }
                    reject(new Error(mensaje));
                },
                {
                    enableHighAccuracy: opciones.enableHighAccuracy !== false,
                    timeout: opciones.timeout || 10000,
                    maximumAge: opciones.maximumAge || 0
                }
            );
        });
    }

    /**
     * Guarda la ubicación GPS de un pedido en el backend.
     * Se llama justo despues de crear un pedido tipo "delivery".
     */
    async function guardarUbicacionPedido(pedidoId, ubicacion) {
        return APICliente.post(`/api/v1/pedidos/${pedidoId}/ubicacion`, {
            lat: ubicacion.lat,
            lng: ubicacion.lng,
            accuracy: ubicacion.accuracy
        });
    }

    return { obtenerUbicacionActual, guardarUbicacionPedido };
})();
