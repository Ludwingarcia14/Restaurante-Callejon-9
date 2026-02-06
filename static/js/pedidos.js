// ===================================
// VARIABLES GLOBALES
// ===================================
let pedidoActual = null;
let pedidosLista = [];
let intervaloActualizacion = null;

// ===================================
// INICIALIZACIÓN
// ===================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('Vista de Pedidos Pendientes inicializada');
    cargarPedidos();
    
    // Actualizar cada 10 segundos
    intervaloActualizacion = setInterval(() => {
        cargarPedidos();
    }, 10000);
    
    // Event listeners
    document.getElementById('sonido-toggle').addEventListener('change', function() {
        console.log('Sonido:', this.checked ? 'Activado' : 'Desactivado');
    });
});

// ===================================
// CARGAR PEDIDOS DESDE API
// ===================================
async function cargarPedidos() {
    try {
        const response = await fetch('/api/cocina/pedidos', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            pedidosLista = data.pedidos;
            renderizarPedidos();
            renderizarListadoRapido();
        }
    } catch (error) {
        console.error('Error cargando pedidos:', error);
    }
}

// ===================================
// RENDERIZAR RECTÁNGULOS DE PEDIDOS
// ===================================
function renderizarPedidos() {
    const contenedor = document.getElementById('contenedor-pedidos');
    
    if (pedidosLista.length === 0) {
        contenedor.innerHTML = `
            <div class="col-span-2 text-center py-16 text-gray-400">
                <i class="bi bi-inbox text-6xl mb-3 block"></i>
                <p class="text-lg font-semibold">Sin pedidos pendientes</p>
                <p class="text-sm mt-1">Los nuevos pedidos aparecerán aquí</p>
            </div>
        `;
        document.getElementById('total-pendientes').textContent = '0';
        return;
    }
    
    contenedor.innerHTML = pedidosLista.map(pedido => crearRectanguloPedido(pedido)).join('');
    document.getElementById('total-pendientes').textContent = pedidosLista.length;
}

// ===================================
// CREAR RECTÁNGULO COMPACTO DE PEDIDO
// ===================================
function crearRectanguloPedido(pedido) {
    const tiempoEsperando = pedido.minutos_esperando;
    const urgencia = tiempoEsperando > 10 ? 'text-red-600 animate-pulse' : 'text-orange-600';
    
    return `
        <div class="bg-white border-l-4 border-red-500 rounded-lg p-4 shadow-md hover:shadow-lg transition">
            <!-- Número Pedido -->
            <div class="flex items-center justify-between mb-3">
                <h4 class="text-2xl font-bold text-gray-800">
                    <i class="bi bi-hash"></i> ${pedido.numero_pedido}
                </h4>
                <span class="px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs font-bold">
                    NUEVO
                </span>
            </div>
            
            <!-- Info Rápida -->
            <div class="grid grid-cols-2 gap-2 mb-3 text-sm">
                <div class="bg-gray-50 p-2 rounded">
                    <p class="text-xs text-gray-600 font-semibold">MESA</p>
                    <p class="font-bold text-gray-800">${pedido.numero_mesa}</p>
                </div>
                <div class="bg-gray-50 p-2 rounded">
                    <p class="text-xs text-gray-600 font-semibold">ENTRADA</p>
                    <p class="font-bold text-gray-800">${pedido.hora_entrada}</p>
                </div>
                <div class="bg-gray-50 p-2 rounded">
                    <p class="text-xs text-gray-600 font-semibold">ESPERANDO</p>
                    <p class="font-bold ${urgencia}">${tiempoEsperando} min</p>
                </div>
                <div class="bg-gray-50 p-2 rounded">
                    <p class="text-xs text-gray-600 font-semibold">REGISTRADO</p>
                    <p class="font-bold text-gray-800 text-xs">${pedido.usuario_registro}</p>
                </div>
            </div>
            
            <!-- Acciones -->
            <div class="flex gap-2">
                <button onclick="verDetallesPedido(${pedido.id})" class="flex-1 px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition font-semibold text-sm">
                    <i class="bi bi-eye"></i> Ver Detalles
                </button>
                <button onclick="iniciarPreparacion(${pedido.id})" class="flex-1 px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition font-semibold text-sm">
                    <i class="bi bi-play-fill"></i> Preparar
                </button>
            </div>
        </div>
    `;
}

// ===================================
// RENDERIZAR LISTADO LATERAL
// ===================================
function renderizarListadoRapido() {
    const listado = document.getElementById('listado-rapido');
    
    if (pedidosLista.length === 0) {
        listado.innerHTML = '<p class="text-sm text-gray-500 text-center py-6">Sin pedidos</p>';
        return;
    }
    
    listado.innerHTML = pedidosLista.map((pedido, index) => `
        <button onclick="verDetallesPedido(${pedido.id})" class="w-full text-left p-2 hover:bg-orange-50 rounded-lg transition border-l-2 border-orange-500">
            <p class="font-bold text-gray-800 text-sm">#${pedido.numero_pedido}</p>
            <p class="text-xs text-gray-600">Mesa ${pedido.numero_mesa}</p>
            <p class="text-xs text-red-600 font-bold mt-1">${pedido.minutos_esperando} min</p>
        </button>
    `).join('');
}

// ===================================
// VER DETALLES DE PEDIDO
// ===================================
async function verDetallesPedido(pedidoId) {
    try {
        const response = await fetch(`/api/cocina/pedidos/${pedidoId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            pedidoActual = data.pedido;
            rellenarModalDetalles(data.pedido);
            document.getElementById('modal-detalles').classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error cargando detalles:', error);
        Swal.fire('Error', 'No se pudieron cargar los detalles', 'error');
    }
}

// ===================================
// RELLENAR MODAL DE DETALLES
// ===================================
function rellenarModalDetalles(pedido) {
    document.getElementById('modal-numero-pedido').textContent = `Pedido #${pedido.numero_pedido}`;
    document.getElementById('modal-numero-mesa').textContent = pedido.numero_mesa;
    document.getElementById('modal-hora-entrada').textContent = pedido.hora_entrada;
    document.getElementById('modal-minutos-esperando').textContent = `${pedido.minutos_esperando} min`;
    document.getElementById('modal-usuario').textContent = pedido.usuario_registro;
    
    // Renderizar platillos
    const contenedorPlatillos = document.getElementById('modal-platillos');
    contenedorPlatillos.innerHTML = pedido.detalles.map(detalle => `
        <div class="bg-gray-50 p-4 rounded-lg border-l-4 border-orange-500">
            <div class="flex items-start justify-between mb-2">
                <div>
                    <p class="font-bold text-gray-800">
                        <span class="text-orange-600 font-bold">${detalle.cantidad}x</span>
                        ${detalle.platillo}
                    </p>
                    <p class="text-sm text-gray-600 mt-1">Precio: $${detalle.precio}</p>
                </div>
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
    `).join('');
}

// ===================================
// ACCIONES DE PEDIDOS
// ===================================
async function iniciarPreparacion(pedidoId) {
    try {
        const response = await fetch(`/api/cocina/pedidos/${pedidoId}/iniciar-preparacion`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            Swal.fire('¡Excelente!', 'Pedido enviado a preparación', 'success');
            cerrarModalDetalles();
            cargarPedidos();
            reproducirSonido();
        } else {
            Swal.fire('Error', data.error || 'No se pudo iniciar la preparación', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire('Error', 'No se pudo iniciar la preparación', 'error');
    }
}

async function iniciarPreparacionDesdeModal() {
    if (pedidoActual) {
        await iniciarPreparacion(pedidoActual.pedido_id);
    }
}

// ===================================
// PLATILLOS NO DISPONIBLES
// ===================================
async function abrirModalNoDisponibles() {
    try {
        const response = await fetch('/api/cocina/platillos-no-disponibles', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            rellenarListaNoDisponibles(data.platillos);
            document.getElementById('modal-no-disponibles').classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error cargando no disponibles:', error);
        Swal.fire('Error', 'No se pudieron cargar los platillos', 'error');
    }
}

function rellenarListaNoDisponibles(platillos) {
    const lista = document.getElementById('lista-no-disponibles');
    
    if (platillos.length === 0) {
        lista.innerHTML = '<p class="text-center text-gray-500 py-6">Todos los platillos disponibles</p>';
        return;
    }
    
    lista.innerHTML = platillos.map(platillo => `
        <div class="bg-yellow-50 p-3 rounded-lg border-l-4 border-yellow-500 flex items-center justify-between">
            <div class="flex-1">
                <p class="font-bold text-gray-800">${platillo.platillo}</p>
                <p class="text-xs text-gray-600 mt-1">Razón: ${platillo.razon}</p>
                <p class="text-xs text-gray-500 mt-1">
                    <i class="bi bi-person"></i> ${platillo.usuario_registro} - ${platillo.fecha_registro}
                </p>
            </div>
            <button onclick="reactivarPlatillo(${platillo.id})" class="px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition text-sm">
                <i class="bi bi-check"></i> Activar
            </button>
        </div>
    `).join('');
}

async function reactivarPlatillo(platilloId) {
    try {
        const response = await fetch(`/api/cocina/platillos/${platilloId}/reactivar`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            Swal.fire('¡Listo!', 'Platillo reactivado', 'success');
            abrirModalNoDisponibles();
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire('Error', 'No se pudo reactivar el platillo', 'error');
    }
}

// ===================================
// UTILIDADES
// ===================================
function cerrarModalDetalles() {
    document.getElementById('modal-detalles').classList.add('hidden');
    pedidoActual = null;
}

function cerrarModalNoDisponibles() {
    document.getElementById('modal-no-disponibles').classList.add('hidden');
}

function reproducirSonido() {
    if (document.getElementById('sonido-toggle').checked) {
        // Sonido de notificación
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    }
}

function actualizarPedidos() {
    Swal.fire({
        title: 'Actualizando...',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
            cargarPedidos();
            setTimeout(() => {
                Swal.close();
            }, 1000);
        }
    });
}

// Limpiar intervalo cuando se abandona la página
window.addEventListener('beforeunload', function() {
    if (intervaloActualizacion) {
        clearInterval(intervaloActualizacion);
    }
});