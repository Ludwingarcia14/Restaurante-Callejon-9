// ==============================================================
// 🔔 SISTEMA DE NOTIFICACIONES - CLIENTES (DASHBOARD EXCLUSIVO)
// ==============================================================

let socketCliente; 

/**
 * 1. LÓGICA DE CONEXIÓN
 * Se conecta y escucha solo eventos relevantes para el cliente.
 */
function conectarSocketCliente(token) {
    // Ajusta la IP si mandas a producción (ej: http://tu-dominio.com:3000)
    socketCliente = io('http://localhost:3000');

    socketCliente.on('connect', () => {
        console.log('[Cliente] ✅ Conectado al sistema de alertas.');
        // Nos registramos para entrar a nuestra "Sala Privada"
        socketCliente.emit('registrar', { token: token }); 
    });

    // --- ESCUCHA DE EVENTOS ---
    socketCliente.on('notificacion', (data) => {
        console.log('[Cliente] 📩 Mensaje recibido:', data);
        
        // CASO A: Se aprobó un documento individual
        if (data.evento === 'DOCUMENTO_APROBADO') {
            mostrarToastCliente(`✅ Tu documento "${data.nombreDoc || 'enviado'}" ha sido aprobado.`, 'success');
            actualizarBadgeCampana();
        
        // CASO B: Se aprobó la carpeta completa (Botón Verde del Asesor)
        } else if (data.evento === 'CARPETA_APROBADA') {
            mostrarToastCliente(`🎉 ¡EXCELENTE! ${data.mensaje}`, 'fiesta');
            actualizarBadgeCampana();
            
            // Opcional: Lanzar efecto de confeti si tienes la librería
            // lanzarConfeti();
        }
    });

    socketCliente.on('disconnect', () => console.log('[Cliente] 🔌 Desconectado.'));
}


/**
 * 2. INTERFAZ VISUAL (UI)
 * Muestra las alertas bonitas en la esquina.
 */
function mostrarToastCliente(mensaje, tipo) {
    const toast = document.createElement('div');
    
    // Estilos base con Tailwind (o CSS inline si no usas Tailwind)
    // Posición fija abajo-derecha, animación suave, encima de todo (z-50)
    toast.className = "fixed bottom-5 right-5 flex items-center p-4 mb-4 w-full max-w-xs text-white rounded-lg shadow-2xl transition-all duration-500 transform translate-y-10 opacity-0 z-50";
    
    // Colores según el tipo de noticia
    if (tipo === 'success') {
        toast.style.backgroundColor = "#10B981"; // Verde Esmeralda
        toast.innerHTML = `<div class="text-2xl mr-3">📄</div><div class="text-sm font-semibold">${mensaje}</div>`;
    } else if (tipo === 'fiesta') {
        toast.style.background = "linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)"; // Gradiente Violeta
        toast.innerHTML = `<div class="text-2xl mr-3">✨</div><div class="text-sm font-bold">${mensaje}</div>`;
    } else {
        toast.style.backgroundColor = "#374151"; // Gris oscuro por defecto
        toast.innerText = mensaje;
    }

    document.body.appendChild(toast);

    // Animación de entrada (Slide Up)
    requestAnimationFrame(() => {
        toast.classList.remove("translate-y-10", "opacity-0");
    });

    // Sonido suave (opcional, comenta si no te gusta)
    try {
        const audio = new Audio('https://assets.mixkit.co/sfx/preview/mixkit-software-interface-start-2574.mp3');
        audio.volume = 0.2;
        audio.play().catch(() => {}); // Ignorar error si el navegador bloquea autoplay
    } catch (e) {}

    // Eliminar después de 6 segundos
    setTimeout(() => {
        toast.classList.add("opacity-0", "translate-y-10"); // Animación salida
        setTimeout(() => toast.remove(), 500);
    }, 6000);
}

/**
 * 3. ACTUALIZAR CAMPANA
 * Busca el ícono de campana en el menú del cliente y le pone un punto rojo/número.
 */
function actualizarBadgeCampana() {
    const badge = document.getElementById('cliente-notificaciones-badge');
    const campanaIcono = document.getElementById('cliente-campana-icono');

    // Si existe el contador (badge)
    if (badge) {
        let cuenta = parseInt(badge.innerText) || 0;
        badge.innerText = cuenta + 1;
        badge.style.display = 'flex'; // Asegura que se vea
        badge.classList.add('animate-pulse'); // Efecto de latido
    }

    // Si existe el ícono, lo agitamos
    if (campanaIcono) {
        campanaIcono.classList.add('text-yellow-400'); // Cambia color temporalmente
        setTimeout(() => campanaIcono.classList.remove('text-yellow-400'), 2000);
    }
}


/**
 * 4. INICIALIZACIÓN AUTOMÁTICA
 * Se ejecuta solo al cargar el script.
 */
async function initSocketCliente() {
    try {
        console.log('🔄 Verificando sesión del cliente...');
        
        // Usamos la ruta segura directa para obtener el token
        const res = await fetch("https://127.0.0.1:5000/api/me-direct/", { 
            credentials: "include" 
        });

        if (!res.ok) return; // Si no está logueado, no hacemos nada silenciosamente.
        
        const data = await res.json();

        // Verificamos que sea tipo 'cliente' (Opcional, extra seguridad)
        if (data.socket_token) {
            conectarSocketCliente(data.socket_token);
        }

    } catch (error) {
        console.error("Error al iniciar notificaciones:", error);
    }
}

// Arrancamos
initSocketCliente();