/**
 * ============================================
 * API CLIENTE - Módulo Móvil
 * Maneja peticiones RESTful usando JWT (Stateless)
 * Depende de: APP.apiUrl (definido en main.js)
 * ============================================
 */

const APICliente = {
    
    // 1. Inyectar el token en las cabeceras
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        const token = localStorage.getItem('access_token');
        if (token) {
            // Limpiar comillas por si se guardó con JSON.stringify
            const cleanToken = token.replace(/^["']|["']$/g, '');
            headers['Authorization'] = `Bearer ${cleanToken}`;
        }
        
        return headers;
    },

    // 2. Motor central de peticiones para el cliente
    async request(endpoint, options = {}) {
        try {
            const url = `${APP.apiUrl}${endpoint}`;
            const config = {
                ...options,
                headers: this.getHeaders(),
                // 'omit' asegura que no enviemos las cookies de sesión 
                // del panel de empleados por accidente
                credentials: 'omit' 
            };

            const response = await fetch(url, config);

            // 3. Interceptar 401 (Token expirado o inválido)
            if (response.status === 401) {
                this.forceLogout();
                throw new Error('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.');
            }

            // Manejo de errores del backend
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `Error HTTP: ${response.status}`);
            }

            const data = await response.json();
            return { success: true, data };

        } catch (error) {
            console.error('[API Cliente] Error:', error.message);
            return { success: false, error: error.message };
        }
    },

    // Métodos de conveniencia
    async get(endpoint) {
        return await this.request(endpoint, { method: 'GET' });
    },

    async post(endpoint, body) {
        return await this.request(endpoint, { 
            method: 'POST', 
            body: JSON.stringify(body) 
        });
    },

    async patch(endpoint, body) {
        return await this.request(endpoint, { 
            method: 'PATCH', 
            body: JSON.stringify(body) 
        });
    },

    // Manejo seguro del cierre de sesión
    forceLogout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Evitar bucles de redirección si ya estamos en el login
        if (window.location.pathname !== '/cliente/login') {
            window.location.href = '/cliente/login';
        }
    }
};