import { API_MEDICIONES } from './api.js';
import { formatearNumero } from './formatters.js';

export async function cargarMediciones() {
    try {
        const response = await fetch(API_MEDICIONES);
        if (!response.ok) throw new Error('No se pudo cargar mediciones');
        const mediciones = await response.json();

        const lista = Array.isArray(mediciones) ? mediciones : (mediciones.results || []);
        const ordenadas = [...lista].sort((a, b) => new Date(b.fecha) - new Date(a.fecha));

        if (!ordenadas.length) {
            document.getElementById('tablaMediciones').innerHTML = '';
            document.getElementById('emptyMediciones').style.display = 'block';
            return;
        }

        document.getElementById('emptyMediciones').style.display = 'none';

        const ultima = ordenadas[0];
        document.getElementById('medTemp').textContent = `${formatearNumero(ultima.temperatura, ' °C')}`;
        document.getElementById('medHum').textContent = `${formatearNumero(ultima.humedad, ' %')}`;
        document.getElementById('medGas').textContent = `${formatearNumero(ultima.gas, ' ppm')}`;
        document.getElementById('medCo').textContent = `${formatearNumero(ultima.co, ' ppm')}`;
        document.getElementById('medRiesgo').textContent = ultima.riesgo || 'Sin dato';

        const filas = ordenadas.slice(0, 8).map((m) => {
            const riesgo = String(m.riesgo || 'Normal');
            const badgeClass = riesgo.toLowerCase().includes('alto') || riesgo.toLowerCase().includes('peligro')
                ? 'badge-danger'
                : riesgo.toLowerCase().includes('medio') || riesgo.toLowerCase().includes('precaucion')
                    ? 'badge-warning'
                    : 'badge-safe';

            return `
                <tr>
                    <td>${new Date(m.fecha).toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' })}</td>
                    <td>${formatearNumero(m.temperatura, ' °C')}</td>
                    <td>${formatearNumero(m.humedad, ' %')}</td>
                    <td>${formatearNumero(m.gas, ' ppm')}</td>
                    <td>${formatearNumero(m.co, ' ppm')}</td>
                    <td><span class="badge-risk ${badgeClass}">${riesgo}</span></td>
                    <td>${m.sensor ?? 'N/A'}</td>
                </tr>
            `;
        }).join('');

        document.getElementById('tablaMediciones').innerHTML = filas;
    } catch (error) {
        console.error('Error cargando mediciones:', error);
    }
}
