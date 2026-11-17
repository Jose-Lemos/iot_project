import { cargarDatos } from './dashboard.js';
import { cargarConfiguracion } from './configuration.js';
import { descargarMediciones } from './measurements.js';
import { configurarChat } from './chat.js';
import { configurarAutenticacion } from './auth.js';

let intervaloDatos = null;
let panelInicializado = false;

function iniciarPanel() {
    if (!panelInicializado) {
        document.querySelectorAll('.nav-btn[data-view]').forEach((button) => {
            button.addEventListener('click', () => {
                document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');

                const view = button.dataset.view;
                document.querySelectorAll('.page').forEach(page => {
                    page.classList.toggle('active', page.id === view);
                });
            });
        });

        document.getElementById('filtroPeriodo').addEventListener('change', cargarDatos);
        document.getElementById('btnDescargarMediciones').addEventListener('click', descargarMediciones);
        configurarChat();
        panelInicializado = true;
    }

    if (intervaloDatos === null) {
        cargarDatos();
        cargarConfiguracion();
        intervaloDatos = setInterval(cargarDatos, 5000);
    }
}

function detenerActualizacion() {
    if (intervaloDatos !== null) {
        clearInterval(intervaloDatos);
        intervaloDatos = null;
    }
}

window.addEventListener('vitalair:auth-expired', detenerActualizacion);
window.addEventListener('vitalair:logged-out', detenerActualizacion);
configurarAutenticacion(iniciarPanel);
