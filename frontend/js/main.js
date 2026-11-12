import { cargarDatos } from './dashboard.js';
import { cargarConfiguracion } from './configuration.js';
import { descargarMediciones } from './measurements.js';

document.querySelectorAll('.nav-btn').forEach((button) => {
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

cargarDatos();
cargarConfiguracion();
setInterval(cargarDatos, 5000);
