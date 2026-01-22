// ========================================
// NOTIFICACIONES EN TIEMPO REAL (Asesor + Cliente)
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
            e.stopPropagation(); // Evita que se cierre inmediatamente
            listaNotificaciones.classList.toggle("hidden");
            
            // Opcional: Limpiar el contador al abrir
            // limpiarContador(); 
        });

        // Cerrar si se hace clic fuera
        document.addEventListener("click", (e) => {
            if (!campana.contains(e.target) && !listaNotificaciones.contains(e.target)) {
                listaNotificaciones.classList.add("hidden");
            }
        });
    }

    // ========================================
    // 2. Limpia el contador (Hacerlo global)
    // ========================================
    window.limpiarContador = function () {
        if (!contador) return;
        contador.classList.add("hidden");
        contador.innerText = "0";
    };

    // ========================================
    // 3. Agregar item a la lista (CON ESTILOS)
    // ========================================
    function agregarNotificacion(mensaje, hora, tipoEvento) {
        if (!listaItems) return;

        // Ocultar mensaje de "No hay notificaciones"
        if (mensajeVacio) mensajeVacio.remove(); // O usa .add('hidden')

        const li = document.createElement("li");
        
        // Estilos base
        let clasesBorde = "border-l-4 border-blue-500"; // Por defecto azul (info)
        
        // Si es aprobado, borde verde
        if (tipoEvento === 'DOCUMENTO_APROBADO') {
            clasesBorde = "border-l-4 border-green-500";
        } else if (tipoEvento === 'RECHAZADO') { // Ejemplo futuro
            clasesBorde = "border-l-4 border-red-500";
        }

        li.className = `px-4 py-3 bg-white hover:bg-gray-50 border-b text-sm animate-pulse transition-all ${clasesBorde}`;
        
        // HTML interno con mensaje y hora
        li.innerHTML = `
            <div class="font-medium text-gray-800">${mensaje}</div>
            <div class="text-xs text-gray-400 mt-1 text-right">${hora || 'Justo ahora'}</div>
        `;

        // Insertar al principio (prepend)
        listaItems.prepend(li);
    }

    // ========================================
    // 4. Aumentar contador y animar
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
    // 6. Conectar a Socket.IO (CORREGIDO)
    // ========================================
    function conectarAlServicioDeNotificaciones(token) {
        // Conexión básica sin auth en handshake (para coincidir con tu server.js actual)
        socket = io("https://pyme-notificaciones.onrender.com/");

        socket.on("connect", () => {
            console.log(`[Socket.io] Conectado. Enviando registro...`);
            
            // --- AQUÍ ESTÁ LA CLAVE: Emitir el evento 'registrar' ---
            socket.emit('registrar', { token: token });
        });

        socket.on("error_autenticacion", (data) => {
            console.error("[Socket.io] Error Auth:", data.msg);
        });

        socket.on("notificacion", (data) => {
            console.log("[Socket.io] Notificación recibida:", data);
            
            // data trae: { evento, mensaje, hora }
            aumentarContador();
            agregarNotificacion(data.mensaje, data.hora, data.evento);
            
            // Opcional: Audio
            // const audio = new Audio('/static/sounds/ding.mp3');
            // audio.play().catch(e => console.log("Audio bloqueado"));
        });

        socket.on("disconnect", () => {
            console.log("[Socket.io] Desconectado.");
        });
    }

    // ========================================
    // 7. Obtener token desde Flask
    // ========================================
    async function iniciarSocket() {
        try {
            console.log("Solicitando datos del usuario...");

            const res = await fetch("http://127.0.0.1:5000/api/me/", {
                method: "GET",
                credentials: "include"
            });

            if (!res.ok) {
                console.warn("Usuario no logueado.");
                return;
            }

            const userData = await res.json();

            if (!userData.socket_token) {
                console.warn("Faltan datos para iniciar sockets.");
                return;
            }

            conectarAlServicioDeNotificaciones(userData.socket_token, userData.rol);

        } catch (err) {
            console.error("Error iniciando sockets:", err.message);
        }
    }

    // Ejecutar inicio
    iniciarSocket();

});