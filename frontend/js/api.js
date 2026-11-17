const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000`;
const TOKEN_KEY = 'vitalairToken';

export const API_ESTADISTICAS = `${API_BASE}/api/alertas/estadisticas/`;
export const API_MEDICIONES = `${API_BASE}/api/mediciones/`;
export const API_ALERTAS = `${API_BASE}/api/alertas/`;
export const API_CONFIG = `${API_BASE}/api/configuracion/`;
export const API_ASISTENTE = `${API_BASE}/asistente/chat/`;
export const API_INGRESO = `${API_BASE}/seguridad/ingreso/`;
export const API_SESION = `${API_BASE}/seguridad/sesion/`;
export const API_CAMBIAR_CONTRASENA = `${API_BASE}/seguridad/cambiar-contrasena/`;
export const API_SALIDA = `${API_BASE}/seguridad/salida/`;

export function obtenerToken() {
    return sessionStorage.getItem(TOKEN_KEY);
}

export function guardarToken(token) {
    sessionStorage.setItem(TOKEN_KEY, token);
}

export function borrarToken() {
    sessionStorage.removeItem(TOKEN_KEY);
}

export async function apiFetch(url, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = obtenerToken();
    if (token) headers.set('Authorization', `Token ${token}`);

    const response = await fetch(url, { ...options, headers });
    if (response.status === 401 && token) {
        borrarToken();
        window.dispatchEvent(new Event('vitalair:auth-expired'));
    }
    return response;
}
