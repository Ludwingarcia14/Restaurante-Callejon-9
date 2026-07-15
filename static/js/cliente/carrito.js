/**
 * ============================================
 * CARRITO DEL CLIENTE - Callejón 9
 * Estado 100% local (localStorage), independiente
 * de los tokens de sesión (access_token/refresh_token).
 * ============================================
 */

const Carrito = (function () {
    const KEY = 'carrito_cliente';

    function obtener() {
        return getFromStorage(KEY, []);
    }

    function guardar(items) {
        saveToStorage(KEY, items);
        actualizarBadge();
    }

    function agregar(platillo, cantidad = 1) {
        const items = obtener();
        const existente = items.find(i => i.platillo_id === platillo.id);

        if (existente) {
            existente.cantidad += cantidad;
        } else {
            items.push({
                platillo_id: platillo.id,
                nombre: platillo.nombre,
                precio: platillo.precio,
                imagen: platillo.imagen || '',
                cantidad: cantidad,
                notas: ''
            });
        }
        guardar(items);
        return items;
    }

    function actualizarCantidad(platillo_id, cantidad) {
        let items = obtener();
        if (cantidad <= 0) {
            items = items.filter(i => i.platillo_id !== platillo_id);
        } else {
            const item = items.find(i => i.platillo_id === platillo_id);
            if (item) item.cantidad = cantidad;
        }
        guardar(items);
        return items;
    }

    function actualizarNotas(platillo_id, notas) {
        const items = obtener();
        const item = items.find(i => i.platillo_id === platillo_id);
        if (item) item.notas = notas;
        guardar(items);
        return items;
    }

    function eliminar(platillo_id) {
        return actualizarCantidad(platillo_id, 0);
    }

    function vaciar() {
        guardar([]);
    }

    function total() {
        return obtener().reduce((sum, i) => sum + (i.precio * i.cantidad), 0);
    }

    function totalItems() {
        return obtener().reduce((sum, i) => sum + i.cantidad, 0);
    }

    function actualizarBadge() {
        const badge = document.getElementById('carrito-badge');
        if (!badge) return;
        const total = totalItems();
        badge.textContent = total > 9 ? '9+' : String(total);
        badge.classList.toggle('hidden', total === 0);
    }

    document.addEventListener('DOMContentLoaded', actualizarBadge);

    return {
        obtener, agregar, actualizarCantidad, actualizarNotas,
        eliminar, vaciar, total, totalItems, actualizarBadge
    };
})();
