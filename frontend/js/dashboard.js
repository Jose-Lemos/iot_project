import { API_ESTADISTICAS } from './api.js';
import { formatearNumero } from './formatters.js';
import { actualizarEstado } from './status.js';
import { renderChart } from './chart.js';
import { renderAlertas } from './alerts.js';
import { cargarMediciones } from './measurements.js';

export async function cargarDatos() {
    const periodo = document.getElementById('filtroPeriodo').value;
    try {
        const response = await fetch(`${API_ESTADISTICAS}?periodo=${periodo}`);
        if (!response.ok) throw new Error('No se pudo obtener la estadística');
        const res = await response.json();

        const temps = res.temperatura || {};
        const hums = res.humedad || {};
        const gases = res.gas || {};
        const grafico = res.grafico || { labels: [], temperatura: [], humedad: [], gas: [], co: [] };

        document.getElementById('tempProm').textContent = formatearNumero(temps.promedio, ' °C');
        document.getElementById('humProm').textContent = formatearNumero(hums.promedio, ' %');
        document.getElementById('gasProm').textContent = formatearNumero(gases.promedio, ' ppm');
        document.getElementById('statAlertas').textContent = res.total_alertas ?? 0;

        const gasActual = grafico.gas && grafico.gas.length ? grafico.gas[grafico.gas.length - 1] : 0;
        document.getElementById('valorActualGas').textContent = `${formatearNumero(gasActual, ' ppm').replace(' ', '')}`;
        actualizarEstado(Number(gasActual));

        renderChart(grafico);
        renderAlertas(periodo);
        cargarMediciones();
    } catch (error) {
        console.error('Error cargando datos:', error);
    }
}
