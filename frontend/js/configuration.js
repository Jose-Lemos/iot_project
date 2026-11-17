import { API_CONFIG, apiFetch } from './api.js';

export async function cargarConfiguracion() {
    try {
        const response = await apiFetch(API_CONFIG);
        if (!response.ok) throw new Error('No se pudo cargar configuración');
        const config = await response.json();
        const campos = [
            ['Temperatura máxima', config.temp_max ?? 35],
            ['Gas máximo', config.gas_max ?? 200],
            ['Humedad mínima', config.humedad_min ?? 20],
        ];
        const contenedor = document.getElementById('configUmbrales');
        contenedor.replaceChildren();
        campos.forEach(([titulo, valor]) => {
            const columna = document.createElement('div');
            columna.className = 'col-md-4';
            const etiqueta = document.createElement('label');
            etiqueta.className = 'form-label fw-semibold';
            etiqueta.textContent = titulo;
            const entrada = document.createElement('input');
            entrada.className = 'form-control';
            entrada.value = String(valor);
            columna.append(etiqueta, entrada);
            contenedor.appendChild(columna);
        });
    } catch (error) {
        console.error('Error cargando configuración:', error);
        const errorMessage = document.createElement('div');
        errorMessage.className = 'alert alert-danger';
        errorMessage.textContent = 'No se pudo recuperar la configuración del sistema.';
        document.getElementById('configUmbrales').replaceChildren(errorMessage);
    }
}
