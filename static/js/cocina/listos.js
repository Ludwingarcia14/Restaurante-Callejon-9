// Lógica para la vista "Pedidos Listos"

let pedidosListos = [];
let pedidoActualListo = null;
let intervaloListos = null;

document.addEventListener('DOMContentLoaded', () => {
    console.log('Vista Pedidos Listos inicializada');
    cargarPedidosListos();

    // Actualizar cada 10s
    intervaloListos = setInterval(cargarPedidosListos, 10000);
});

// Cargar pedidos listos desde la API
async function cargarPedidosListos() {
    try {
        const res = await fetch('/api/cocina/pedidos/listos', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.success) {
            pedidosListos = data.pedidos;
            renderizarListos();
            renderizarListadoRapidoListos();
        }
    } catch (err) {
        console.error('Error cargando pedidos listos:', err);
    }
}

// Renderizar tarjetas de pedidos listos
function renderizarListos() {
    const cont = document.getElementById('contenedor-listos');
    if (!cont) return;

    if (!pedidosListos || pedidosListos.length === 0) {
        cont.innerHTML = `
            <div class="col-span-2 text-center py-16 text-gray-400">
                <i class="bi bi-inbox text-6xl mb-3 block"></i>
                <p class="text-lg font-semibold">Sin pedidos listos</p>
                <p class="text-sm mt-1">Los pedidos listos aparecerán aquí</p>
            </div>
        `;
        const totalEl = document.getElementById('total-listos');
        if (totalEl) totalEl.textContent = '0';
        return;
    }

    cont.innerHTML = pedidosListos.map(p => crearRectanguloListo(p)).join('');
    const totalEl = document.getElementById('total-listos');
    if (totalEl) totalEl.textContent = String(pedidosListos.length);
}

// Crear tarjeta para un pedido listo
function crearRectanguloListo(pedido) {
    const tiempo = pedido.minutos_esperando ?? 0;
    return `
        <div class="bg-white border-l-4 border-green-500 rounded-lg p-4 shadow-md hover:shadow-lg transition">
            <div class="flex items-center justify-between mb-3">
                <h4 class="text-2xl font-bold text-gray-800"><i class="bi bi-hash"></i> ${pedido.numero_pedido}</h4>
                <span class="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-bold">LISTO</span>
            </div>

            <div class="grid grid-cols-2 gap-2 mb-3 text-sm">
                <div class="bg-white p-2 rounded">
                    <p class="text-xs text-gray-600 font-semibold">MESA</p>
                    <p class="font-bold text-gray-800">${pedido.numero_mesa}</p>
                </div>
                <div class="bg-white p-2 rounded">
                    <p class="text-xs text-gray-600 font-semibold">ENTRADA</p>
                    <p class="font-bold text-gray-800">${pedido.hora_entrada || '--:--'}</p>
                </div>
                <div class="bg-white p-2 rounded">
                    <p class="text-xs text-gray-600 font-semibold">TIEMPO</p>
                    <p class="font-bold text-green-600">${tiempo} min</p>
                </div>
                <div class="bg-white p-2 rounded">
                    <p class="text-xs text-gray-600 font-semibold">TOTAL</p>
                    <p class="font-bold text-gray-800">$${pedido.total_cuenta ?? '0.00'}</p>
                </div>
            </div>

            <div class="flex gap-2">
                <button onclick="verDetallesListos(${pedido.id})" class="flex-1 px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition font-semibold text-sm">
                    <i class="bi bi-eye"></i> Ver Detalles
                </button>
                <button onclick="confirmarEntregaDesdeRectangulo(${pedido.id})" class="flex-1 px-3 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:shadow-lg transition font-semibold text-sm">
                    <i class="bi bi-send"></i> Entregar
                </button>
            </div>
        </div>
    `;
}

// Listado lateral rápido
function renderizarListadoRapidoListos() {
    const listado = document.getElementById('listado-rapido-listos');
    if (!listado) return;

    if (!pedidosListos || pedidosListos.length === 0) {
        listado.innerHTML = '<p class="text-sm text-gray-500 text-center py-6">Sin pedidos</p>';
        return;
    }

    listado.innerHTML = pedidosListos.map(p => `
        <button onclick="verDetallesListos(${p.id})" class="w-full text-left p-2 hover:bg-green-50 rounded-lg transition border-l-2 border-green-500">
            <p class="font-bold text-gray-800 text-sm">#${p.numero_pedido}</p>
            <p class="text-xs text-gray-600">Mesa ${p.numero_mesa}</p>
            <p class="text-xs text-green-600 font-bold mt-1">${p.minutos_esperando ?? 0} min</p>
        </button>
    `).join('');
}

// Obtener y mostrar detalles de pedido listo
async function verDetallesListos(pedidoId) {
    try {
        const res = await fetch(`/api/cocina/pedidos/${pedidoId}`, { method: 'GET', headers: { 'Content-Type': 'application/json' } });
        const data = await res.json();
        if (data.success) {
            pedidoActualListo = data.pedido;
            rellenarModalListos(data.pedido);
            const modal = document.getElementById('modal-detalles-listos');
            if (modal) modal.classList.remove('hidden');
        } else {
            Swal.fire('Error', data.error || 'Pedido no encontrado', 'error');
        }
    } catch (err) {
        console.error('Error cargando detalles listos:', err);
        Swal.fire('Error', 'No se pudieron cargar los detalles', 'error');
    }
}

// Llenar modal con información del pedido listo
function rellenarModalListos(pedido) {
    const num = document.getElementById('modal-listos-numero-pedido');
    const mesa = document.getElementById('modal-listos-numero-mesa');
    const tiempoTotal = document.getElementById('modal-listos-tiempo-total');
    const totalCuenta = document.getElementById('modal-listos-total-cuenta');
    const contPlatillos = document.getElementById('modal-listos-platillos');

    if (num) num.textContent = `Pedido #${pedido.numero_pedido}`;
    if (mesa) mesa.textContent = pedido.numero_mesa;
    if (tiempoTotal) tiempoTotal.textContent = `${pedido.minutos_esperando ?? '--'} min`;
    if (totalCuenta) totalCuenta.textContent = `$${pedido.total_cuenta ?? '0.00'}`;

    if (contPlatillos) {
        contPlatillos.innerHTML = (pedido.detalles || []).map(d => `
            <div class="bg-white p-4 rounded-lg border-l-4 border-green-300">
                <div class="flex items-start justify-between">
                    <div>
                        <p class="font-bold text-gray-800">${d.cantidad}x ${d.platillo}</p>
                        <p class="text-sm text-gray-600 mt-1">Precio: $${d.precio}</p>
                        ${d.notas_especiales ? `<p class="text-xs text-gray-700 mt-2"><strong>Notas:</strong> ${d.notas_especiales}</p>` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    }
}

// Confirmar entrega (desde modal)
async function confirmarEntregaDesdeModal() {
    if (!pedidoActualListo) return;
    await confirmarEntrega(pedidoActualListo.pedido_id ?? pedidoActualListo.id);
}

// Confirmar entrega (desde tarjeta)
async function confirmarEntregaDesdeRectangulo(pedidoId) {
    await confirmarEntrega(pedidoId);
}

// Llamada API para confirmar entrega (end-point genérico)
async function confirmarEntrega(pedidoId) {
    try {
        // Endpoint hipotético: ajustar según backend
        const res = await fetch(`/api/cocina/pedidos/${pedidoId}/entregar`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.success) {
            Swal.fire('¡Hecho!', 'Pedido entregado', 'success');
            cerrarModalDetallesListos();
            cargarPedidosListos();
        } else {
            Swal.fire('Error', data.error || 'No se pudo confirmar la entrega', 'error');
        }
    } catch (err) {
        console.error('Error confirmando entrega:', err);
        Swal.fire('Error', 'No se pudo confirmar la entrega', 'error');
    }
}

function cerrarModalDetallesListos() {
    const modal = document.getElementById('modal-detalles-listos');
    if (modal) modal.classList.add('hidden');
    pedidoActualListo = null;
}

function actualizarListos() {
    Swal.fire({
        title: 'Actualizando...',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
            cargarPedidosListos();
            setTimeout(() => Swal.close(), 800);
        }
    });
}

// Limpiar intervalo al salir
window.addEventListener('beforeunload', () => {
    if (intervaloListos) clearInterval(intervaloListos);
});