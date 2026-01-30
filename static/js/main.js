/**
 * ============================================
 * 🍽️ CALLEJÓN 9 - SISTEMA DE RESTAURANTE
 * Scripts Principales
 * ============================================
 */

// ===== CONFIGURACIÓN GLOBAL =====
const APP = {
    name: 'Callejón 9',
    version: '1.0.0',
    apiUrl: window.location.origin,
    debug: true
};

// ===== FUNCIONES DE UTILIDAD =====

/**
 * Log personalizado para debugging
 */
function log(message, type = 'info') {
    if (!APP.debug) return;
    
    const styles = {
        info: 'background: #3b82f6; color: white',
        success: 'background: #10b981; color: white',
        warning: 'background: #f59e0b; color: white',
        error: 'background: #ef4444; color: white'
    };
    
    console.log(`%c ${APP.name} `, styles[type] || styles.info, message);
}

/**
 * Formatear moneda
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN'
    }).format(amount);
}

/**
 * Formatear fecha
 */
function formatDate(date, includeTime = false) {
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };
    
    if (includeTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
    }
    
    return new Intl.DateTimeFormat('es-MX', options).format(new Date(date));
}

/**
 * Debounce function para optimizar eventos
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ===== PETICIONES HTTP =====

/**
 * Función genérica para peticiones fetch
 */
async function fetchAPI(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include'
    };
    
    const config = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(`${APP.apiUrl}${endpoint}`, config);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return { success: true, data };
        
    } catch (error) {
        log(`Error en petición: ${error.message}`, 'error');
        return { success: false, error: error.message };
    }
}

/**
 * GET request
 */
async function getData(endpoint) {
    return await fetchAPI(endpoint, { method: 'GET' });
}

/**
 * POST request
 */
async function postData(endpoint, data) {
    return await fetchAPI(endpoint, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

/**
 * PUT request
 */
async function putData(endpoint, data) {
    return await fetchAPI(endpoint, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

/**
 * DELETE request
 */
async function deleteData(endpoint) {
    return await fetchAPI(endpoint, { method: 'DELETE' });
}

// ===== NOTIFICACIONES Y ALERTAS =====

/**
 * Mostrar notificación toast
 */
function showToast(message, type = 'success') {
    Swal.fire({
        icon: type,
        title: message,
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer);
            toast.addEventListener('mouseleave', Swal.resumeTimer);
        }
    });
}

/**
 * Mostrar alerta de confirmación
 */
async function confirmDialog(title, text) {
    const result = await Swal.fire({
        title: title,
        text: text,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#667eea',
        cancelButtonColor: '#ef4444',
        confirmButtonText: 'Sí, continuar',
        cancelButtonText: 'Cancelar'
    });
    
    return result.isConfirmed;
}

/**
 * Mostrar alerta de éxito
 */
function showSuccess(message, title = '¡Éxito!') {
    Swal.fire({
        icon: 'success',
        title: title,
        text: message,
        confirmButtonColor: '#667eea'
    });
}

/**
 * Mostrar alerta de error
 */
function showError(message, title = 'Error') {
    Swal.fire({
        icon: 'error',
        title: title,
        text: message,
        confirmButtonColor: '#667eea'
    });
}

/**
 * Mostrar loading
 */
function showLoading(message = 'Cargando...') {
    Swal.fire({
        title: message,
        allowOutsideClick: false,
        allowEscapeKey: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
}

/**
 * Cerrar loading
 */
function hideLoading() {
    Swal.close();
}

// ===== VALIDACIÓN DE FORMULARIOS =====

/**
 * Validar email
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(String(email).toLowerCase());
}

/**
 * Validar teléfono (México)
 */
function validatePhone(phone) {
    const re = /^(\+52)?[\s-]?(\d{10})$/;
    return re.test(String(phone));
}

/**
 * Validar formulario
 */
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('border-red-500');
            isValid = false;
        } else {
            input.classList.remove('border-red-500');
        }
    });
    
    return isValid;
}

// ===== MANIPULACIÓN DEL DOM =====

/**
 * Crear elemento HTML
 */
function createElement(tag, className, content) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (content) element.textContent = content;
    return element;
}

/**
 * Toggle de clase
 */
function toggleClass(selector, className) {
    const element = document.querySelector(selector);
    if (element) {
        element.classList.toggle(className);
    }
}

/**
 * Mostrar/ocultar elemento
 */
function toggleElement(selector) {
    const element = document.querySelector(selector);
    if (element) {
        element.classList.toggle('hidden');
    }
}

// ===== GESTIÓN DE LOCAL STORAGE =====

/**
 * Guardar en localStorage
 */
function saveToStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (error) {
        log(`Error guardando en localStorage: ${error.message}`, 'error');
        return false;
    }
}

/**
 * Obtener de localStorage
 */
function getFromStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        log(`Error leyendo localStorage: ${error.message}`, 'error');
        return defaultValue;
    }
}

/**
 * Eliminar de localStorage
 */
function removeFromStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (error) {
        log(`Error eliminando de localStorage: ${error.message}`, 'error');
        return false;
    }
}

// ===== FUNCIONES DE TABLA =====

/**
 * Buscar en tabla
 */
function searchTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!input || !table) return;
    
    input.addEventListener('keyup', debounce(function() {
        const filter = this.value.toUpperCase();
        const rows = table.getElementsByTagName('tr');
        
        for (let i = 1; i < rows.length; i++) {
            const row = rows[i];
            const cells = row.getElementsByTagName('td');
            let found = false;
            
            for (let j = 0; j < cells.length; j++) {
                const cell = cells[j];
                if (cell) {
                    const textValue = cell.textContent || cell.innerText;
                    if (textValue.toUpperCase().indexOf(filter) > -1) {
                        found = true;
                        break;
                    }
                }
            }
            
            row.style.display = found ? '' : 'none';
        }
    }, 300));
}

/**
 * Ordenar tabla
 */
function sortTable(tableId, columnIndex) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.getElementsByTagName('tbody')[0];
    const rows = Array.from(tbody.getElementsByTagName('tr'));
    
    rows.sort((a, b) => {
        const aValue = a.getElementsByTagName('td')[columnIndex].textContent;
        const bValue = b.getElementsByTagName('td')[columnIndex].textContent;
        
        return aValue.localeCompare(bValue, 'es', { numeric: true });
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

// ===== COPIAR AL PORTAPAPELES =====

/**
 * Copiar texto al portapapeles
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Copiado al portapapeles', 'success');
        return true;
    } catch (error) {
        log(`Error copiando al portapapeles: ${error.message}`, 'error');
        showToast('Error al copiar', 'error');
        return false;
    }
}

// ===== GESTIÓN DE ARCHIVOS =====

/**
 * Convertir archivo a base64
 */
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
}

/**
 * Validar tamaño de archivo
 */
function validateFileSize(file, maxSizeMB = 5) {
    const maxSize = maxSizeMB * 1024 * 1024;
    return file.size <= maxSize;
}

/**
 * Validar tipo de archivo
 */
function validateFileType(file, allowedTypes) {
    return allowedTypes.includes(file.type);
}

// ===== INICIALIZACIÓN =====

document.addEventListener('DOMContentLoaded', function() {
    log('Sistema inicializado correctamente', 'success');
    
    // Inicializar tooltips si existen
    initTooltips();
    
    // Marcar link activo
    markActiveLink();
});

/**
 * Inicializar tooltips
 */
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const text = this.getAttribute('data-tooltip');
            const tooltip = createElement('div', 'tooltip', text);
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
            tooltip.style.left = `${rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2)}px`;
        });
        
        element.addEventListener('mouseleave', function() {
            const tooltips = document.querySelectorAll('.tooltip');
            tooltips.forEach(t => t.remove());
        });
    });
}

/**
 * Marcar link activo en navegación
 */
function markActiveLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// ===== EXPORTAR FUNCIONES GLOBALES =====
window.APP = APP;
window.log = log;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.showToast = showToast;
window.confirmDialog = confirmDialog;
window.showSuccess = showSuccess;
window.showError = showError;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.getData = getData;
window.postData = postData;
window.putData = putData;
window.deleteData = deleteData;