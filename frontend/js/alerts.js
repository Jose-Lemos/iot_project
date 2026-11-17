import { API_ALERTAS, apiFetch } from './api.js';

export async function renderAlertas(periodo) {
    try {
        const response = await apiFetch(`${API_ALERTAS}?periodo=${periodo}`);
        if (!response.ok) throw new Error('No se pudo cargar alertas');
        const alertas = await response.json();
        const lista = Array.isArray(alertas) ? alertas : (alertas.results || []);
        const contenedor = document.getElementById('listaAlertas');
        contenedor.replaceChildren();
        if (!lista.length) {
            const vacio = document.createElement('div');
            vacio.className = 'alert alert-secondary';
            vacio.textContent = 'No hay alertas para este período.';
            contenedor.appendChild(vacio);
            return;
        }

        lista.slice(0, 5).forEach((alerta) => {
            const tarjeta = document.createElement('div');
            tarjeta.className = 'alert alert-light border rounded-4 mb-3';
            const encabezado = document.createElement('div');
            encabezado.className = 'd-flex justify-content-between align-items-center';
            const tipo = document.createElement('strong');
            tipo.textContent = alerta.tipo || 'Alerta';
            const estado = document.createElement('span');
            estado.className = `badge bg-${alerta.atendida ? 'success' : 'warning'} text-${alerta.atendida ? 'white' : 'dark'}`;
            estado.textContent = alerta.atendida ? 'Atendida' : 'Activa';
            encabezado.append(tipo, estado);

            const descripcion = document.createElement('p');
            descripcion.className = 'mb-1 mt-2 text-muted';
            descripcion.textContent = alerta.descripcion || 'Sin descripción';
            const fecha = document.createElement('small');
            fecha.textContent = new Date(alerta.fecha).toLocaleString('es-AR');
            tarjeta.append(encabezado, descripcion, fecha);
            contenedor.appendChild(tarjeta);
        });
    } catch (error) {
        console.error('Error cargando alertas:', error);
        const mensajeError = document.createElement('div');
        mensajeError.className = 'alert alert-danger';
        mensajeError.textContent = 'No se pudo cargar la información de alertas.';
        document.getElementById('listaAlertas').replaceChildren(mensajeError);
    }
}
