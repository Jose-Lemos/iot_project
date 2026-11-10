import { API_ALERTAS } from './api.js';

export async function renderAlertas(periodo) {
    try {
        const response = await fetch(`${API_ALERTAS}?periodo=${periodo}`);
        if (!response.ok) throw new Error('No se pudo cargar alertas');
        const alertas = await response.json();
        const lista = Array.isArray(alertas) ? alertas : (alertas.results || []);

        const html = lista.length
            ? lista.slice(0, 5).map((alerta) => `
                <div class="alert alert-light border rounded-4 mb-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <strong>${alerta.tipo || 'Alerta'}</strong>
                        <span class="badge bg-${alerta.atendida ? 'success' : 'warning'} text-${alerta.atendida ? 'white' : 'dark'}">
                            ${alerta.atendida ? 'Atendida' : 'Activa'}
                        </span>
                    </div>
                    <p class="mb-1 mt-2 text-muted">${alerta.descripcion || 'Sin descripción'}</p>
                    <small>${new Date(alerta.fecha).toLocaleString('es-AR')}</small>
                </div>
            `).join('')
            : '<div class="alert alert-secondary">No hay alertas para este período.</div>';

        document.getElementById('listaAlertas').innerHTML = html;
    } catch (error) {
        console.error('Error cargando alertas:', error);
        document.getElementById('listaAlertas').innerHTML = '<div class="alert alert-danger">No se pudo cargar la información de alertas.</div>';
    }
}
