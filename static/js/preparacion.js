// ===================================
// VARIABLES GLOBALES
// ===================================
let pedidoActualPrep = null;
let pedidosPreparacion = [];
let intervaloPrep = null;

// ===================================
// INICIALIZACIÓN
// ===================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('Vista de Preparación inicializada');
    cargarPedidosPreparacion();
    
    // Actualizar cada 5 segundos
    intervaloPrep = setInterval(() => {
        cargarPedidosPreparacion();
    }, 5000);
});

// ===================================
// CARGAR PEDIDOS EN PREPARACIÓN
// ===================================
async function cargarPedidosPreparacion() {
    try {
        const response = await fetch('/api/cocina/pedidos/preparacion', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            pedidosPreparacion = data.pedidos;
            renderizarPreparacion();
            renderizarListadoRapidoPrep();
        }
    } catch (error) {
        console.error('Error cargando preparación:', error);
    }
}

// ===================================
// RENDERIZAR RECTÁNGULOS CON ESTADOS
// ===================================
function renderizarPreparacion() {
    const contenedor = document.getElementById('contenedor-preparacion');
    
    if (pedidosPreparacion.length === 0) {
        contenedor.innerHTML = `
            <div class="col-span-2 text-center py-16 text-gray-400">
                <i class="bi bi-inbox text-6xl mb-3 block"></i>
                <p class="text-lg font-semibold">Sin pedidos en preparación</p>
                <p class="text-sm mt-1">Los pedidos aparecerán aquí cuando se inicie su preparación</p>
            </div>
        `;
        document.getElementById('total-preparacion').textContent = '0';
        return;
    }
    
    contenedor.innerHTML = pedidosPreparacion.map(pedido => crearRectanguloPreparacion(pedido)).join('');
    document.getElementById('total-preparacion').textContent = pedidosPreparacion.length;
}

// ===================================
// CREAR RECTÁNGULO CON ESTADO VERDE/ROJO
// ===================================
function crearRectanguloPreparacion(pedido) {
    const tiempoEsperando = pedido.minutos_esperando;
    const urgencia = tiempoEsperando > 15 ? 'border-red-500 bg-red-50' : 'border-orange-500 bg-orange-50';
    
    return `
        <div class="bg-white border-l-4 ${urgencia} rounded-lg p-4 shadow-md hover:shadow-lg transition">
            <!-- Número Pedido -->
            <div class="flex items-center justify-between mb-3">
                <h4 class="text-2xl font-bold text-gray-800">
                    <i class="bi bi-hash"></i> ${pedido.numero_pedido}
                </h4>
                <span class="px-3 py-1 ${tiempoEsperando > 15 ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'} rounded-full text-xs font-bold">
                    EN COCINA
                </span>
            </div>
            
            <!-- Info Rápida -->
            <div class="grid grid-cols-2 gap-2 mb-3 text-sm">
                <div class="bg-white p-2 rounded">
                    <p class="text-xs text-gray-600 font-semibold">MESA</p>
                    <p class="font-bold text-gray-800">${pedido.numero_mesa}</p>
                </div>
                <div class="bg-white p-2 rounded">
                    <p class="text-xs text-gray-600 font-semibold">ENTRADA</p>
                    <p class="font-bold text-gray-800">${pedido.hora_entrada}</p>
                </div>
                <div class="bg-white p-2 rounded">
                    <p class="text-xs text-gray-600 font-semibold">ESPERANDO</p>
                    <p class="font-bold ${tiempoEsperando > 15 ? 'text-red-600 animate-pulse' : 'text-orange-600'}">${tiempoEsperando} min</p>
                </div>
                <div class="bg-white p-2 rounded">
                    <p class="text-xs text-gray-600 font-semibold">TOTAL</p>
                    <p class="font-bold text-gray-800">$${pedido.total_cuenta}</p>
                </div>
            </div>
            
            <!-- Acciones -->
            <div class="flex gap-2">
                <button onclick="verDetallesPrep(${pedido.id})" class="flex-1 px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition font-semibold text-sm">
                    <i class="bi bi-eye"></i> Ver Detalles
                </button>
                <button onclick="marcarListoDesdeRectangulo(${pedido.id})" class="flex-1 px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition font-semibold text-sm">
                    <i class="bi bi-check-circle"></i> Listo
                </button>
            </div>
        </div>
    `;
}

// ===================================
// RENDERIZAR LISTADO LATERAL
// ===================================
function renderizarListadoRapidoPrep() {
    const listado = document.getElementById('listado-rapido-prep');
    
    if (pedidosPreparacion.length === 0) {
        listado.innerHTML = '<p class="text-sm text-gray-500 text-center py-6">Sin pedidos</p>';
        return;
    }
    
    listado.innerHTML = pedidosPreparacion.map((pedido) => {
        const tiempoEsperando = pedido.minutos_esperando;
        const colorUrgencia = tiempoEsperando > 15 ? 'border-red-500 bg-red-50' : 'border-orange-500 bg-orange-50';
        
        return `
            <button onclick="verDetallesPrep(${pedido.id})" class="w-full text-left p-2 hover:bg-opacity-80 rounded-lg transition border-l-2 ${colorUrgencia}">
                <p class="font-bold text-gray-800 text-sm">#${pedido.numero_pedido}</p>
                <p class="text-xs text-gray-600">Mesa ${pedido.numero_mesa}</p>
                <p class="text-xs font-bold mt-1 ${tiempoEsperando > 15 ? 'text-red-600 animate-pulse' : 'text-orange-600'}">${tiempoEsperando} min</p>
            </button>
        `;
    }).join('');
}

// ===================================
// VER DETALLES Y CAMBIAR ESTADO
// ===================================
async function verDetallesPrep(pedidoId) {
    try {
        const response = await fetch(`/api/cocina/pedidos/${pedidoId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            pedidoActualPrep = data.pedido;
            rellenarModalPreparacion(data.pedido);
            document.getElementById('modal-detalles-prep').classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire('Error', 'No se pudieron cargar los detalles', 'error');
    }
}

// ===================================
// RELLENAR MODAL DE PREPARACIÓN
// ===================================
function rellenarModalPreparacion(pedido) {
    document.getElementById('modal-prep-numero-pedido').textContent = `Pedido #${pedido.numero_pedido}`;
    document.getElementById('modal-prep-numero-mesa').textContent = pedido.numero_mesa;
    document.getElementById('modal-prep-tiempo').textContent = `-- min`;
    document.getElementById('modal-prep-total-tiempo').textContent = `${pedido.minutos_esperando} min`;
    document.getElementById('modal-prep-estado-general').textContent = 'En Preparación';
    
    // Renderizar platillos con estados (Verde = Listo, Rojo = No iniciado)
    const contenedorPlatillos = document.getElementById('modal-prep-platillos');
    contenedorPlatillos.innerHTML = pedido.detalles.map(detalle => {
        const estadoColor = detalle.estado_preparacion === 'listo' ? 
            'bg-green-50 border-green-500' : 'bg-red-50 border-red-500';
        const estadoIcon = detalle.estado_preparacion === 'listo' ?
            '<i class="bi bi-check-circle text-green-600"></i>' : 
            '<i class="bi bi-circle text-red-600"></i>';
        
        return `
            <div class="bg-white p-4 rounded-lg border-l-4 ${estadoColor}">
                <div class="flex items-start justify-between mb-2">
                    <div class="flex-1">
                        <p class="font-bold text-gray-800">
                            ${estadoIcon}
                            <span class="ml-2">${detalle.cantidad}x ${detalle.platillo}</span>
                        </p>
                        <p class="text-sm text-gray-600 mt-1">Precio: $${detalle.precio}</p>
                    </div>
                    <select onchange="cambiarEstadoPlatillo(${detalle.id}, this.value)" class="px-2 py-1 text-xs border rounded">
                        <option value="no_iniciado" ${detalle.estado_preparacion === 'no_iniciado' ? 'selected' : ''}>No Iniciado</option>
                        <option value="preparando" ${detalle.estado_preparacion === 'preparando' ? 'selected' : ''}>Preparando</option>
                        <option value="listo" ${detalle.estado_preparacion === 'listo' ? 'selected' : ''}>Listo</option>
                    </select>
                </div>
                ${detalle.notas_especiales ? `
                    <div class="mt-2 p-2 bg-yellow-50 border-l-2 border-yellow-500 rounded">
                        <p class="text-sm text-gray-700">
                            <i class="bi bi-exclamation-circle text-yellow-600"></i>
                            <strong>Notas:</strong> ${detalle.notas_especiales}
                        </p>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

// ===================================
// CAMBIAR ESTADO DE PLATILLO
// ===================================
async function cambiarEstadoPlatillo(detalleId, nuevoEstado) {
    try {
        const response = await fetch(`/api/cocina/detalles/${detalleId}/estado`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ estado: nuevoEstado })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('Estado actualizado');
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire('Error', 'No se pudo actualizar el estado', 'error');
    }
}

// ===================================
// MARCAR TODO COMO LISTO
// ===================================
async function marcarTodoListoDesdeModal() {
    if (!pedidoActualPrep) return;
    await marcarListoDesdeRectangulo(pedidoActualPrep.pedido_id);
}

async function marcarListoDesdeRectangulo(pedidoId) {
    try {
        const response = await fetch(`/api/cocina/pedidos/${pedidoId}/marcar-listo`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            Swal.fire('¡Perfecto!', 'Pedido marcado como listo', 'success');
            cerrarModalDetallesPrep();
            cargarPedidosPreparacion();
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire('Error', 'No se pudo marcar como listo', 'error');
    }
}

// ===================================
// UTILIDADES
// ===================================
function cerrarModalDetallesPrep() {
    document.getElementById('modal-detalles-prep').classList.add('hidden');
    pedidoActualPrep = null;
}

function actualizarPreparacion() {
    Swal.fire({
        title: 'Actualizando...',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
            cargarPedidosPreparacion();
            setTimeout(() => {
                Swal.close();
            }, 1000);
        }
    });
}

// Limpiar intervalo cuando se abandona la página
window.addEventListener('beforeunload', function() {
    if (intervaloPrep) {
        clearInterval(intervaloPrep);
    }
});