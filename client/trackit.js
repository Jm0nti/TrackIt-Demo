// --- CONFIGURACIÓN ---
// DEBES REEMPLAZAR ESTA URL con la dirección de tu API FastAPI (generalmente http://127.0.0.1:8000)
const API_BASE_URL = "http://127.0.0.1:8000"; 
        
let currentTrackingId = null;
let intervalId = null;
const POLLING_INTERVAL = 5000; // 5 segundos

// --- REFERENCIAS DOM ---
const trackingInput = document.getElementById('trackingInput');
const searchButton = document.getElementById('searchButton');
const messageArea = document.getElementById('messageArea');
const shipmentDetails = document.getElementById('shipmentDetails');
const toggleRealtimeButton = document.getElementById('toggleRealtime'); 
const realtimeControls = document.getElementById('realtimeControls');
        
// --- FUNCIONES DE UTILIDAD ---

/**
 * Convierte un timestamp (segundos desde el epoch) recibido del backend
 * a un formato amigable (dd/mm/yyyy:hh:mm:ss).
 * * NOTA IMPORTANTE: JavaScript usa milisegundos, por lo que multiplicamos por 1000.
 * * @param {number} timestamp - Segundos desde el Epoch.
 * @returns {string} Tiempo formateado.
 */
function formatBogotaTime(timestamp) {
    if (typeof timestamp !== 'number' || isNaN(timestamp)) {
        console.error("Entrada inválida para timestamp:", timestamp);
        return 'Fecha no disponible'; // Fallback si no es un número válido
    }
    
    // Convertir segundos a milisegundos para el constructor de Date
    const date = new Date(timestamp * 1000);

    if (isNaN(date.getTime())) {
        console.error("Fallo al crear objeto Date con timestamp:", timestamp);
        return 'Fecha no disponible';
    }

    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0'); // Meses son 0-indexados
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    // Formato solicitado: dd/mm/año:hh:mm:ss
    return `${day}/${month}/${year}:${hours}:${minutes}:${seconds}`;
}


/**
 * Muestra un mensaje en el área de mensajes.
 * @param {string} text - El texto del mensaje.
 * @param {boolean} [isError=false] - Si es un mensaje de error, aplica estilos rojos.
 */
function displayMessage(text, isError = false) {
    messageArea.textContent = text;
    messageArea.className = `p-3 rounded-lg text-sm transition-all duration-300 ${isError ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`;
    messageArea.classList.remove('hidden');
}

/** Oculta el área de mensajes. */
function hideMessage() {
    messageArea.classList.add('hidden');
}

/**
 * Aplica estilos de color al estado normalizado.
 * @param {string} status - El estado normalizado (ej: 'DELIVERED').
 */
function setStatusColor(status) {
    const statusElement = document.getElementById('normalizedStatus');
    statusElement.className = 'text-2xl font-extrabold';
    
    switch(status) {
        case 'DELIVERED':
            statusElement.classList.add('text-green-600');
            break;
        case 'IN_TRANSIT':
            statusElement.classList.add('text-yellow-600');
            break;
        case 'AT_WAREHOUSE':
            statusElement.classList.add('text-blue-600');
            break;
        case 'DELIVERY_ATTEMPT_FAILED':
            statusElement.classList.add('text-red-600');
            break;
        default:
            statusElement.classList.add('text-gray-600');
    }
}

/**
 * Renderiza los datos normalizados del envío en la interfaz.
 * @param {object} data - El objeto TrackItShipment normalizado.
 */
function renderShipment(data) {
    document.getElementById('trackingIdDisplay').textContent = `ID: ${data.tracking_id}`;
    document.getElementById('normalizedStatus').textContent = data.normalized_status;
    document.getElementById('friendlyStatus').textContent = data.friendly_status;
    document.getElementById('carrierName').textContent = data.carrier_name;
    // MODIFICACIÓN CLAVE: Se pasa el valor float (timestamp) a la función de formato
    document.getElementById('lastUpdate').textContent = formatBogotaTime(data.last_update);
    document.getElementById('location').textContent = 
        `Lat: ${data.current_location.latitude.toFixed(4)}, Lng: ${data.current_location.longitude.toFixed(4)}`;

    setStatusColor(data.normalized_status);
    shipmentDetails.classList.remove('hidden');
    realtimeControls.classList.remove('hidden');
}

/**
 * Inicia el proceso de sondeo (polling) para una actualización en tiempo real.
 * @param {string} id - El ID de seguimiento.
 */
function startPolling(id) {
    // Limpia cualquier intervalo anterior
    stopPolling(); 
    currentTrackingId = id;

    // Inicia el sondeo
    intervalId = setInterval(() => {
        fetchShipment(id, true); // true indica que es una actualización silenciosa
    }, POLLING_INTERVAL);
    
    // Configura el botón para detener
    toggleRealtimeButton.textContent = `Detener Actualización (Poll: 5s)`;
    toggleRealtimeButton.classList.replace('bg-green-100', 'bg-red-100');
    toggleRealtimeButton.classList.replace('text-green-600', 'text-red-600');
    toggleRealtimeButton.onclick = stopPolling;
}

/** Detiene el proceso de sondeo (polling). */
function stopPolling() {
    if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
    }
    // Configura el botón para iniciar
    toggleRealtimeButton.textContent = `Iniciar Actualización (Poll: 5s)`;
    toggleRealtimeButton.classList.replace('bg-red-100', 'bg-green-100');
    toggleRealtimeButton.classList.replace('text-red-600', 'text-green-600');
    // Solo si hay un ID actual, permite reiniciar el polling
    if (currentTrackingId) {
        toggleRealtimeButton.onclick = () => startPolling(currentTrackingId);
    } else {
        toggleRealtimeButton.onclick = null;
    }
}

/**
 * Fetchea los datos del envío de la API y maneja la normalización.
 * @param {string} id - El ID de seguimiento.
 * @param {boolean} [isUpdate=false] - Si es una actualización de sondeo.
 */
async function fetchShipment(id, isUpdate = false) {
    if (!id) return;

    searchButton.disabled = true;
    if (!isUpdate) {
        // Solo para la búsqueda inicial, limpia y muestra el mensaje de carga
        hideMessage();
        shipmentDetails.classList.add('hidden');
        realtimeControls.classList.add('hidden');
        displayMessage("Buscando y normalizando datos...", false);
    }

    const url = `${API_BASE_URL}/api/v1/track/${id}`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();

        if (!response.ok) {
            // Maneja errores de la API (404, 429, 500)
            throw new Error(data.detail || `Error ${response.status}: Error desconocido`);
        }

        // El JSON retornado ES EL OBJETO TrackItShipment NORMALIZADO
        renderShipment(data);
        
        if (!isUpdate) {
            displayMessage(`¡Envío ${id} normalizado con éxito!`, false);
            startPolling(id); // Inicia el sondeo solo después de la primera búsqueda exitosa
        }

    } catch (error) {
        stopPolling();
        const errorMessage = `Fallo en la Integración: ${error.message}`;
        displayMessage(errorMessage, true);
        console.error(error);
    } finally {
        searchButton.disabled = false;
    }
}

// --- EVENT LISTENERS ---

// Evento al hacer click en el botón de búsqueda
searchButton.addEventListener('click', () => {
    const id = trackingInput.value.trim().toUpperCase();
    if (id) {
        fetchShipment(id);
    } else {
        displayMessage("Por favor, ingrese un ID de seguimiento válido.", true);
    }
});

// Detener el sondeo al cargar la página (seguridad)
window.onload = stopPolling;
