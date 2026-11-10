import { API_CONFIG } from './api.js';

export async function cargarConfiguracion() {
    try {
        const response = await fetch(API_CONFIG);
        if (!response.ok) throw new Error('No se pudo cargar configuración');
        const config = await response.json();
        document.getElementById('configUmbrales').innerHTML = `
            <div class="col-md-4">
                <label class="form-label fw-semibold">Temperatura máxima</label>
                <input class="form-control" value="${config.temp_max ?? 35}" />
            </div>
            <div class="col-md-4">
                <label class="form-label fw-semibold">Gas máximo</label>
                <input class="form-control" value="${config.gas_max ?? 200}" />
            </div>
            <div class="col-md-4">
                <label class="form-label fw-semibold">Humedad mínima</label>
                <input class="form-control" value="${config.humedad_min ?? 20}" />
            </div>
        `;
    } catch (error) {
        console.error('Error cargando configuración:', error);
        document.getElementById('configUmbrales').innerHTML = '<div class="alert alert-danger">No se pudo recuperar la configuración del sistema.</div>';
    }
}
