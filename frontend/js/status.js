import { obtenerClaseEstado } from './formatters.js';

export function actualizarEstado(ppm) {
    const estado = obtenerClaseEstado(ppm);
    const estadoAire = document.getElementById('estadoAire');
    const mensajeEstado = document.getElementById('mensajeEstado');

    if (!estadoAire || !mensajeEstado) return;

    estadoAire.textContent = estado.texto;
    estadoAire.className = `estado ${estado.clase}`;
    mensajeEstado.textContent = estado.mensaje;

    const statusHome = document.getElementById('statusHome');
    if (statusHome) {
        statusHome.style.background = ppm < 25
            ? 'linear-gradient(135deg, rgba(34,197,94,0.12), rgba(59,130,246,0.07))'
            : ppm < 50
                ? 'linear-gradient(135deg, rgba(245,158,11,0.13), rgba(250,204,21,0.08))'
                : 'linear-gradient(135deg, rgba(239,68,68,0.12), rgba(251,146,60,0.08))';
    }
}
