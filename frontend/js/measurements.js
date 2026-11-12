import { API_MEDICIONES } from './api.js';
import { formatearNumero } from './formatters.js';

const DURACION_PERIODO = {
    diario: 24 * 60 * 60 * 1000,
    semanal: 7 * 24 * 60 * 60 * 1000,
    mensual: 30 * 24 * 60 * 60 * 1000,
    anual: 365 * 24 * 60 * 60 * 1000
};

const NOMBRE_PERIODO = {
    diario: 'dia',
    semanal: 'semana',
    mensual: 'mes',
    anual: 'anio'
};

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

function escaparXml(valor) {
    return String(valor)
        .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&apos;');
}

function crearCelda(valor, tipo = 'String', estilo = '') {
    const atributoEstilo = estilo ? ` ss:StyleID="${estilo}"` : '';
    return `<Cell${atributoEstilo}><Data ss:Type="${tipo}">${escaparXml(valor)}</Data></Cell>`;
}

function crearLibroExcel(mediciones) {
    const encabezados = ['Fecha', 'Temperatura (°C)', 'Humedad (%)', 'Gas (ppm)', 'CO (ppm)', 'Riesgo', 'Sensor'];
    const filas = mediciones.map((medicion) => {
        const fecha = new Date(medicion.fecha).toISOString();
        const valores = [
            crearCelda(fecha, 'DateTime', 'fecha'),
            ...['temperatura', 'humedad', 'gas', 'co'].map((campo) => {
                const dato = medicion[campo];
                const valor = Number(dato);
                return dato !== null && dato !== undefined && dato !== '' && Number.isFinite(valor)
                    ? crearCelda(valor, 'Number')
                    : '<Cell/>';
            }),
            crearCelda(medicion.riesgo || 'Sin dato'),
            crearCelda(medicion.sensor ?? 'N/A')
        ];
        return `<Row>${valores.join('')}</Row>`;
    }).join('');

    return `<?xml version="1.0" encoding="UTF-8"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
 <Styles>
  <Style ss:ID="encabezado"><Font ss:Bold="1"/><Interior ss:Color="#DCEBFF" ss:Pattern="Solid"/></Style>
  <Style ss:ID="fecha"><NumberFormat ss:Format="dd/mm/yyyy hh:mm:ss"/></Style>
 </Styles>
 <Worksheet ss:Name="Mediciones">
  <Table>
   <Row>${encabezados.map((valor) => crearCelda(valor, 'String', 'encabezado')).join('')}</Row>
   ${filas}
  </Table>
 </Worksheet>
</Workbook>`;
}

export async function descargarMediciones() {
    const boton = document.getElementById('btnDescargarMediciones');
    const periodo = document.getElementById('filtroPeriodo').value;
    const duracion = DURACION_PERIODO[periodo];

    if (!duracion) {
        window.alert('Seleccioná un período válido para descargar las mediciones.');
        return;
    }

    boton.disabled = true;
    boton.textContent = 'Preparando archivo...';

    try {
        const response = await fetch(API_MEDICIONES);
        if (!response.ok) throw new Error('No se pudieron obtener las mediciones.');
        const respuesta = await response.json();
        const mediciones = Array.isArray(respuesta) ? respuesta : (respuesta.results || []);
        const ahora = Date.now();
        const inicio = ahora - duracion;
        const filtradas = mediciones
            .filter((medicion) => {
                const fecha = new Date(medicion.fecha).getTime();
                return Number.isFinite(fecha) && fecha >= inicio && fecha <= ahora;
            })
            .sort((a, b) => new Date(a.fecha) - new Date(b.fecha));

        if (!filtradas.length) {
            window.alert('No hay mediciones registradas para el período seleccionado.');
            return;
        }

        const contenido = crearLibroExcel(filtradas);
        const archivo = new Blob([contenido], { type: 'application/vnd.ms-excel;charset=utf-8' });
        const url = URL.createObjectURL(archivo);
        const enlace = document.createElement('a');
        const fechaArchivo = new Date().toLocaleDateString('sv-SE');
        enlace.href = url;
        enlace.download = `mediciones_${NOMBRE_PERIODO[periodo]}_${fechaArchivo}.xls`;
        document.body.appendChild(enlace);
        enlace.click();
        enlace.remove();
        window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) {
        console.error('Error descargando mediciones:', error);
        window.alert('No se pudieron descargar las mediciones. Revisá la conexión con el servidor e intentá nuevamente.');
    } finally {
        boton.disabled = false;
        boton.textContent = 'Descargar Excel';
    }
}
