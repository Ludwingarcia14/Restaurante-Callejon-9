// ========================================
// NOTIFICACIONES EN TIEMPO REAL - RESTAURANTE CALLEJÓN 9
// Sistema de notificaciones diferenciadas por rol
// ========================================

document.addEventListener("DOMContentLoaded", function () {

    let socket;

    // UI Elements
    const campana = document.getElementById("btnNotificaciones");
    const listaNotificaciones = document.getElementById("listaNotificaciones");
    const listaItems = document.getElementById("lista-items-notificaciones");
    const contador = document.getElementById("contador-notificaciones");
    const mensajeVacio = document.getElementById("sin-notificaciones");

    // ========================================
    // 1. Manejo del toggle del menú
    // ========================================
    if (campana && listaNotificaciones) {
        campana.addEventListener("click", (e) => {
            e.stopPropagation();
            listaNotificaciones.classList.toggle("hidden");
            
            // Cargar notificaciones al abrir
            if (!listaNotificaciones.classList.contains("hidden")) {
                cargarNotificaciones();
            }
        });

        // Cerrar si se hace clic fuera
        document.addEventListener("click", (e) => {
            if (!campana.contains(e.target) && !listaNotificaciones.contains(e.target)) {
                listaNotificaciones.classList.add("hidden");
            }
        });
    }

    // ========================================
    // 2. Limpia el contador
    // ========================================
    window.limpiarContador = function () {
        if (!contador) return;
        contador.classList.add("hidden");
        contador.innerText = "0";
    };

    // ========================================
    // 3. Actualizar contador desde servidor
    // ========================================
    async function actualizarContador() {
        try {
            const res = await fetch("/api/notificaciones/contador", {
                method: "GET",
                credentials: "include"
            });

            if (!res.ok) return;

            const data = await res.json();
            
            if (data.success && data.count > 0) {
                if (contador) {
                    contador.innerText = data.count;
                    contador.classList.remove("hidden");
                }
            } else {
                limpiarContador();
            }
        } catch (err) {
            console.error("Error actualizando contador:", err);
        }
    }

    // ========================================
    // 4. Cargar notificaciones desde la API
    // ========================================
    async function cargarNotificaciones() {
        try {
            const res = await fetch("/api/notificaciones/no-leidas", {
                method: "GET",
                credentials: "include"
            });

            if (!res.ok) return;

            const data = await res.json();
            
            if (data.success && data.notificaciones.length > 0) {
                // Limpiar lista
                if (listaItems) {
                    listaItems.innerHTML = "";
                }

                // Ocultar mensaje vacío
                if (mensajeVacio) {
                    mensajeVacio.classList.add("hidden");
                }

                // Agregar notificaciones
                data.notificaciones.forEach(notif => {
                    const fecha = new Date(notif.fecha);
                    const horaFormateada = fecha.toLocaleTimeString('es-MX', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                    });
                    
                    agregarNotificacion(
                        notif.mensaje, 
                        horaFormateada, 
                        notif.tipo,
                        notif._id
                    );
                });
            } else {
                // Mostrar mensaje vacío
                if (mensajeVacio) {
                    mensajeVacio.classList.remove("hidden");
                }
            }
        } catch (err) {
            console.error("Error cargando notificaciones:", err);
        }
    }

    // ========================================
    // 5. Agregar item a la lista CON ESTILOS
    // ========================================
    function agregarNotificacion(mensaje, hora, tipoEvento, notifId) {
        if (!listaItems) return;

        // Ocultar mensaje de "No hay notificaciones"
        if (mensajeVacio) mensajeVacio.classList.add("hidden");

        const li = document.createElement("li");
        li.dataset.notifId = notifId || "";
        
        // Configuración de estilos según tipo de evento
        const estilosEvento = obtenerEstilosPorTipo(tipoEvento);
        
        li.className = `px-4 py-3 bg-white hover:bg-gray-50 border-b text-sm transition-all cursor-pointer ${estilosEvento.clasesBorde}`;
        
        // HTML interno con icono, mensaje y hora
        li.innerHTML = `
            <div class="flex items-start gap-3">
                <span class="text-xl flex-shrink-0">${estilosEvento.icono}</span>
                <div class="flex-1 min-w-0">
                    <div class="font-medium text-gray-800 break-words">${mensaje}</div>
                    <div class="text-xs text-gray-400 mt-1">${hora || 'Justo ahora'}</div>
                </div>
                <button class="btn-marcar-leida text-gray-400 hover:text-green-600 flex-shrink-0" title="Marcar como leída">
                    <i class="fas fa-check"></i>
                </button>
            </div>
        `;

        // Event listener para marcar como leída
        const btnMarcarLeida = li.querySelector('.btn-marcar-leida');
        if (btnMarcarLeida && notifId) {
            btnMarcarLeida.addEventListener('click', async (e) => {
                e.stopPropagation();
                await marcarComoLeida(notifId, li);
            });
        }

        // Insertar al principio (prepend)
        listaItems.prepend(li);

        // Animación de entrada
        setTimeout(() => {
            li.style.animation = 'slideIn 0.3s ease-out';
        }, 10);
    }

    // ========================================
    // 6. Obtener estilos según tipo de evento
    // ========================================
    function obtenerEstilosPorTipo(tipo) {
        const estilos = {
            'LOGIN': { 
                clasesBorde: 'border-l-4 border-green-500', 
                icono: '🔐' 
            },
            'LOGOUT': { 
                clasesBorde: 'border-l-4 border-gray-500', 
                icono: '🚪' 
            },
            'ERROR_SISTEMA': { 
                clasesBorde: 'border-l-4 border-red-500', 
                icono: '⚠️' 
            },
            'BACKUP_CREADO': { 
                clasesBorde: 'border-l-4 border-blue-500', 
                icono: '💾' 
            },
            'BACKUP_RESTAURADO': { 
                clasesBorde: 'border-l-4 border-purple-500', 
                icono: '🔄' 
            },
            'EMPLEADO_CREADO': { 
                clasesBorde: 'border-l-4 border-green-500', 
                icono: '👤' 
            },
            'EMPLEADO_ELIMINADO': { 
                clasesBorde: 'border-l-4 border-red-500', 
                icono: '❌' 
            },
            'ALERTA_INVENTARIO': { 
                clasesBorde: 'border-l-4 border-yellow-500', 
                icono: '📦' 
            },
            'PEDIDO_NUEVO': { 
                clasesBorde: 'border-l-4 border-orange-500', 
                icono: '🔔' 
            },
            'PEDIDO_LISTO': { 
                clasesBorde: 'border-l-4 border-green-500', 
                icono: '✅' 
            },
            'STOCK_BAJO': { 
                clasesBorde: 'border-l-4 border-red-500', 
                icono: '📉' 
            },
            'ENTRADA_REGISTRADA': { 
                clasesBorde: 'border-l-4 border-green-500', 
                icono: '📥' 
            },
            'SALIDA_REGISTRADA': { 
                clasesBorde: 'border-l-4 border-orange-500', 
                icono: '📤' 
            },
            'MERMA_REGISTRADA': { 
                clasesBorde: 'border-l-4 border-red-500', 
                icono: '🗑️' 
            }
        };

        return estilos[tipo] || { 
            clasesBorde: 'border-l-4 border-blue-500', 
            icono: 'ℹ️' 
        };
    }

    // ========================================
    // 7. Marcar notificación como leída
    // ========================================
    async function marcarComoLeida(notifId, elementoLi) {
        try {
            const res = await fetch(`/api/notificaciones/${notifId}/leida`, {
                method: "PUT",
                credentials: "include"
            });

            if (res.ok) {
                // Animar y remover
                elementoLi.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => {
                    elementoLi.remove();
                    
                    // Verificar si quedan notificaciones
                    if (listaItems && listaItems.children.length === 0) {
                        if (mensajeVacio) {
                            mensajeVacio.classList.remove("hidden");
                        }
                    }
                    
                    // Actualizar contador
                    actualizarContador();
                }, 300);
            }
        } catch (err) {
            console.error("Error marcando como leída:", err);
        }
    }

    // ========================================
    // 8. Aumentar contador y animar
    // ========================================
    function aumentarContador() {
        if (!contador) return;
        
        let actual = parseInt(contador.innerText) || 0;
        contador.innerText = actual + 1;
        contador.classList.remove("hidden");

        // Animación de rebote en la campana
        if (campana) {
            campana.classList.add('animate-bounce');
            setTimeout(() => campana.classList.remove('animate-bounce'), 1000);
        }
    }

    // ========================================
    // 9. Reproducir sonido de notificación
    // ========================================
    function reproducirSonido() {
        try {
            // Crear sonido simple con Web Audio API
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

    // ========================================
    // 10. Conectar a Socket.IO
    // ========================================
    function conectarAlServicioDeNotificaciones(token) {
const SOCKET_URL = window.location.origin;
socket = io(SOCKET_URL, {
    transports: ['polling', 'websocket'],
    timeout: 10000
});
        socket.on("connect", () => {
            console.log(`[Socket.io] ✅ Conectado. Enviando registro...`);
            socket.emit('registrar', { token: token });
        });

        socket.on("error_autenticacion", (data) => {
            console.error("[Socket.io] ❌ Error Auth:", data.msg);
        });

        socket.on("notificacion", (data) => {
            console.log("[Socket.io] 📬 Notificación recibida:", data);
            
            // Aumentar contador
            aumentarContador();
            
            // Agregar a la lista
            agregarNotificacion(
                data.mensaje, 
                data.hora || new Date().toLocaleTimeString('es-MX', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                }), 
                data.evento
            );
            
            // Reproducir sonido
            reproducirSonido();
            
            // Mostrar notificación del navegador si está permitido
            if ("Notification" in window && Notification.permission === "granted") {
                new Notification("Restaurante Callejón 9", {
                    body: data.mensaje,
                    icon: "/static/img/logo.png",
                    tag: data.evento
                });
            }
        });

        socket.on("disconnect", () => {
            console.log("[Socket.io] ⚠️ Desconectado.");
        });

        socket.on("reconnect", (attemptNumber) => {
            console.log(`[Socket.io] 🔄 Reconectado después de ${attemptNumber} intentos`);
            actualizarContador();
        });
    }

    // ========================================
    // 11. Solicitar permisos de notificación
    // ========================================
    async function solicitarPermisosNotificacion() {
        if ("Notification" in window && Notification.permission === "default") {
            try {
                const permission = await Notification.requestPermission();
                console.log("Permiso de notificaciones:", permission);
            } catch (err) {
                console.log("No se pudieron solicitar permisos de notificación");
            }
        }
    }

    // ========================================
    // 12. Obtener token y iniciar socket
    // ========================================
    async function iniciarSocket() {
        try {
            console.log("🔍 Solicitando datos del usuario...");

            const res = await fetch("/api/me", {
                method: "GET",
                credentials: "include"
            });

            if (!res.ok) {
                console.warn("⚠️ Usuario no logueado.");
                return;
            }

            const userData = await res.json();

            if (!userData.socket_token) {
                console.warn("⚠️ Faltan datos para iniciar sockets.");
                return;
            }

            console.log("✅ Datos de usuario obtenidos:", {
                nombre: userData.nombre,
                rol: userData.rol
            });

            // Solicitar permisos de notificación
            await solicitarPermisosNotificacion();

            // Conectar al servicio de notificaciones
            conectarAlServicioDeNotificaciones(userData.socket_token);

            // Actualizar contador inicial
            await actualizarContador();

        } catch (err) {
            console.error("❌ Error iniciando sockets:", err.message);
        }
    }

    // ========================================
    // 13. Marcar todas como leídas (opcional)
    // ========================================
    window.marcarTodasLeidas = async function() {
        try {
            const res = await fetch("/api/notificaciones/marcar-todas-leidas", {
                method: "POST",
                credentials: "include"
            });

            if (res.ok) {
                // Limpiar lista
                if (listaItems) {
                    listaItems.innerHTML = "";
                }
                
                // Mostrar mensaje vacío
                if (mensajeVacio) {
                    mensajeVacio.classList.remove("hidden");
                }
                
                // Limpiar contador
                limpiarContador();
            }
        } catch (err) {
            console.error("Error marcando todas como leídas:", err);
        }
    };

    // ========================================
    // 14. Inicialización
    // ========================================
    
    // Ejecutar inicio
    iniciarSocket();

    // Actualizar contador cada 30 segundos
    setInterval(actualizarContador, 30000);

});

// ========================================
// CSS Animations (Agregar al archivo CSS)
// ========================================
/*
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes slideOut {
    from {
        opacity: 1;
        transform: translateX(0);
    }
    to {
        opacity: 0;
        transform: translateX(20px);
    }
}
*/