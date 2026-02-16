// ========================================
// NOTIFICACIONES EN HEADER - RESTAURANTE CALLEJON 9
// Sistema de notificaciones en tiempo real
// ========================================

document.addEventListener("DOMContentLoaded", function () {

    let socket;
    const trigger = document.getElementById('notification-trigger');
    const dropdown = document.getElementById('notification-dropdown');
    const list = document.getElementById('notification-list');
    const noNotifications = document.getElementById('no-notifications');
    const countBadge = document.getElementById('notification-count');

    // Iconos por tipo de evento
    const iconos = {
        'LOGIN': { class: 'fas fa-sign-in-alt', color: 'text-green-500' },
        'LOGOUT': { class: 'fas fa-sign-out-alt', color: 'text-gray-500' },
        'ERROR_SISTEMA': { class: 'fas fa-exclamation-triangle', color: 'text-red-500' },
        'BACKUP_CREADO': { class: 'fas fa-save', color: 'text-blue-500' },
        'BACKUP_RESTAURADO': { class: 'fas fa-sync', color: 'text-purple-500' },
        'EMPLEADO_CREADO': { class: 'fas fa-user-plus', color: 'text-green-500' },
        'EMPLEADO_ELIMINADO': { class: 'fas fa-user-minus', color: 'text-red-500' },
        'ALERTA_INVENTARIO': { class: 'fas fa-boxes', color: 'text-yellow-500' },
        'PEDIDO_NUEVO': { class: 'fas fa-utensils', color: 'text-orange-500' },
        'PEDIDO_LISTO': { class: 'fas fa-check-circle', color: 'text-green-500' },
        'STOCK_BAJO': { class: 'fas fa-exclamation-circle', color: 'text-red-500' },
        'ENTRADA_REGISTRADA': { class: 'fas fa-arrow-down', color: 'text-green-500' },
        'SALIDA_REGISTRADA': { class: 'fas fa-arrow-up', color: 'text-orange-500' },
        'MERMA_REGISTRADA': { class: 'fas fa-trash', color: 'text-red-500' }
    };

    // Toggle dropdown
    if (trigger && dropdown) {
        trigger.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            dropdown.classList.toggle('hidden');
            
            if (!dropdown.classList.contains('hidden')) {
                cargarNotificaciones();
            }
        });

        document.addEventListener('click', function (e) {
            if (!trigger.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.classList.add('hidden');
            }
        });
    }

    // Cargar notificaciones desde la API
    async function cargarNotificaciones() {
        try {
            const res = await fetch("/api/notificaciones/no-leidas", {
                method: "GET",
                credentials: "include"
            });

            if (!res.ok) return;

            const data = await res.json();
            
            if (data.success && data.notificaciones.length > 0) {
                renderizarNotificaciones(data.notificaciones);
                actualizarContador(data.notificaciones.length);
            } else {
                sinNotificaciones();
            }
        } catch (err) {
            console.error("Error cargando notificaciones:", err);
        }
    }

    // Renderizar notificaciones
    function renderizarNotificaciones(notificaciones) {
        if (!list) return;
        
        list.innerHTML = '';
        
        notificaciones.forEach(notif => {
            let fecha;
            
            // Manejar diferentes formatos de fecha
            if (typeof notif.fecha === 'string') {
                // Si la fecha ya viene con timezone (contiene + o Z), parsearla directamente
                if (notif.fecha.includes('+') || notif.fecha.endsWith('Z')) {
                    fecha = new Date(notif.fecha);
                } else {
                    // Agregar timezone de Mexico para fechas sin timezone
                    fecha = new Date(notif.fecha + '-06:00');
                }
            } else {
                fecha = new Date(notif.fecha);
            }
            
            // Formatear fecha y hora en hora local de Mexico
            const fechaFormateada = fecha.toLocaleDateString('es-MX', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                timeZone: 'America/Mexico_City'
            });
            
            const horaFormateada = fecha.toLocaleTimeString('es-MX', { 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit',
                timeZone: 'America/Mexico_City'
            });
            
            const iconoInfo = iconos[notif.tipo] || { class: 'fas fa-info-circle', color: 'text-blue-500' };
            
            const item = document.createElement('div');
            item.className = 'notification-item unread flex items-start gap-3';
            item.dataset.id = notif._id;
            
            item.innerHTML = `
                <span class="${iconoInfo.color} mt-1">
                    <i class="${iconoInfo.class}"></i>
                </span>
                <div class="flex-1 min-w-0">
                    <p class="text-sm text-gray-800 break-words">${notif.mensaje}</p>
                    <p class="text-xs text-gray-400 mt-1">${fechaFormateada} - ${horaFormateada}</p>
                </div>
                <button class="btn-marcar-leida text-gray-400 hover:text-green-600 transition" title="Marcar como leida">
                    <i class="fas fa-check"></i>
                </button>
            `;
            
            // Evento para marcar como leida
            const btn = item.querySelector('.btn-marcar-leida');
            if (btn && notif._id) {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    await marcarComoLeida(notif._id, item);
                });
            }
            
            list.appendChild(item);
        });
    }

    // Sin notificaciones
    function sinNotificaciones() {
        if (!noNotifications) return;
        noNotifications.classList.remove('hidden');
        if (list) list.innerHTML = '';
        ocultarContador();
    }

    // Actualizar contador
    function actualizarContador(num) {
        if (!countBadge) return;
        
        if (num > 0) {
            countBadge.textContent = num > 99 ? '99+' : num;
            countBadge.classList.remove('hidden');
        } else {
            ocultarContador();
        }
    }

    // Ocultar contador
    function ocultarContador() {
        if (countBadge) countBadge.classList.add('hidden');
    }

    // Marcar como leida
    async function marcarComoLeida(notifId, elemento) {
        try {
            const res = await fetch(`/api/notificaciones/${notifId}/leida`, {
                method: "PUT",
                credentials: "include"
            });

            if (res.ok) {
                elemento.style.opacity = '0';
                elemento.style.transform = 'translateX(20px)';
                elemento.style.transition = 'all 0.3s ease';
                
                setTimeout(() => {
                    elemento.remove();
                    
                    // Verificar si quedan notificaciones
                    if (list && list.children.length === 0) {
                        sinNotificaciones();
                    }
                    
                    // Actualizar contador
                    const count = parseInt(countBadge?.textContent || '0');
                    actualizarContador(Math.max(0, count - 1));
                }, 300);
            }
        } catch (err) {
            console.error("Error marcando como leida:", err);
        }
    }

    // Marcar todas como leidas
    window.marcarTodasLeidas = async function () {
        try {
            const res = await fetch("/api/notificaciones/marcar-todas-leidas", {
                method: "POST",
                credentials: "include"
            });

            if (res.ok) {
                sinNotificaciones();
                ocultarContador();
            }
        } catch (err) {
            console.error("Error marcando todas como leidas:", err);
        }
    };

    // Aumentar contador
    function aumentarContador() {
        if (!countBadge) return;
        
        let actual = parseInt(countBadge.textContent) || 0;
        countBadge.textContent = actual + 1;
        countBadge.classList.remove('hidden');

        // Animacion de rebote
        if (trigger) {
            trigger.classList.add('animate-bounce');
            setTimeout(() => trigger.classList.remove('animate-bounce'), 1000);
        }
    }

    // Reproducir sonido
    function reproducirSonido() {
        try {
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
        } catch (e) {
            console.log("Audio no disponible");
        }
    }

    // Conectar a Socket.IO
    function conectarAlServicioDeNotificaciones(token) {
        const SOCKET_URL = window.location.origin;
        socket = io(SOCKET_URL, {
            transports: ['polling', 'websocket'],
            timeout: 10000
        });
        
        socket.on("connect", () => {
            console.log("[Socket.io] Conectado");
            socket.emit('registrar', { token: token });
        });

        socket.on("error_autenticacion", (data) => {
            console.error("[Socket.io] Error Auth:", data.msg);
        });

        socket.on("notificacion", (data) => {
            console.log("[Socket.io] Notificacion recibida:", data);
            
            aumentarContador();
            
            // Agregar nueva notificacion al inicio
            if (list) {
                noNotifications?.classList.add('hidden');
                
                const iconoInfo = iconos[data.evento] || { class: 'fas fa-info-circle', color: 'text-blue-500' };
                
                const item = document.createElement('div');
                item.className = 'notification-item unread flex items-start gap-3';
                item.dataset.id = data.id || '';
                
                item.innerHTML = `
                    <span class="${iconoInfo.color} mt-1">
                        <i class="${iconoInfo.class}"></i>
                    </span>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm text-gray-800 break-words">${data.mensaje}</p>
                        <p class="text-xs text-gray-400 mt-1">Ahora</p>
                    </div>
                    <button class="btn-marcar-leida text-gray-400 hover:text-green-600 transition">
                        <i class="fas fa-check"></i>
                    </button>
                `;
                
                list.insertBefore(item, list.firstChild);
            }
            
            reproducirSonido();
            
            // Notificacion del navegador
            if ("Notification" in window && Notification.permission === "granted") {
                new Notification("Restaurante Callejon 9", {
                    body: data.mensaje,
                    icon: "/static/img/logo.png",
                    tag: data.evento
                });
            }
        });

        socket.on("disconnect", () => {
            console.log("[Socket.io] Desconectado");
        });

        socket.on("reconnect", (attemptNumber) => {
            console.log(`[Socket.io] Reconectado despues de ${attemptNumber} intentos`);
            cargarNotificaciones();
        });
    }

    // Solicitar permisos de notificacion
    async function solicitarPermisosNotificacion() {
        if ("Notification" in window && Notification.permission === "default") {
            try {
                await Notification.requestPermission();
            } catch (err) {
                console.log("No se pudieron solicitar permisos de notificacion");
            }
        }
    }

    // Iniciar Socket
    async function iniciarSocket() {
        try {
            const res = await fetch("/api/me", {
                method: "GET",
                credentials: "include"
            });

            if (!res.ok) return;

            const userData = await res.json();

            if (!userData.socket_token) return;

            await solicitarPermisosNotificacion();
            conectarAlServicioDeNotificaciones(userData.socket_token);
            await cargarNotificaciones();

        } catch (err) {
            console.error("Error iniciando sockets:", err.message);
        }
    }

    // Inicializar
    iniciarSocket();

    // Actualizar contador cada 30 segundos
    setInterval(cargarNotificaciones, 30000);

});
