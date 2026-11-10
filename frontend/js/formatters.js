export function formatearNumero(valor, sufijo = '') {
    const numero = Number(valor ?? 0);
    return Number.isFinite(numero) ? `${numero.toFixed(1)}${sufijo}` : `0${sufijo}`;
}

export function obtenerClaseEstado(ppm) {
    if (ppm < 25) return { texto: '🟢 SEGURO', clase: 'text-success', mensaje: 'El ambiente presenta condiciones normales.' };
    if (ppm < 50) return { texto: '🟡 PRECAUCIÓN', clase: 'text-warning', mensaje: 'Se recomienda ventilar el ambiente y verificar el funcionamiento de los equipos.' };
    if (ppm < 100) return { texto: '🟠 RIESGO', clase: 'text-warning', mensaje: 'Hay una concentración elevada de gas. Se recomienda actuar con precaución.' };
    return { texto: '🔴 PELIGRO', clase: 'text-danger', mensaje: 'Peligro crítico: evacuar el área y contactar a emergencias.' };
}
