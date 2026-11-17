import {
    API_CAMBIAR_CONTRASENA,
    API_INGRESO,
    API_SALIDA,
    API_SESION,
    apiFetch,
    borrarToken,
    guardarToken,
    obtenerToken,
} from './api.js';

function mensajeDeError(datos, mensajeAlternativo) {
    if (datos.error) return datos.error;
    if (datos.detail) return datos.detail;
    return Object.values(datos).flat().join(' ') || mensajeAlternativo;
}

export function configurarAutenticacion(alIniciar) {
    const pantalla = document.getElementById('authScreen');
    const aplicacion = document.getElementById('appShell');
    const formularioIngreso = document.getElementById('loginForm');
    const formularioCambio = document.getElementById('changePasswordForm');
    const mensaje = document.getElementById('authMessage');

    function mostrarMensaje(texto = '') {
        mensaje.textContent = texto;
        mensaje.hidden = !texto;
    }

    function mostrarIngreso(texto = '') {
        aplicacion.hidden = true;
        pantalla.hidden = false;
        formularioIngreso.hidden = false;
        formularioCambio.hidden = true;
        mostrarMensaje(texto);
    }

    function mostrarCambioContrasena() {
        aplicacion.hidden = true;
        pantalla.hidden = false;
        formularioIngreso.hidden = true;
        formularioCambio.hidden = false;
        mostrarMensaje('');
    }

    function mostrarAplicacion() {
        pantalla.hidden = true;
        aplicacion.hidden = false;
        mostrarMensaje('');
        alIniciar();
    }

    formularioIngreso.addEventListener('submit', async (event) => {
        event.preventDefault();
        const boton = document.getElementById('loginSubmit');
        boton.disabled = true;
        mostrarMensaje('');
        try {
            const response = await fetch(API_INGRESO, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: document.getElementById('loginUsername').value,
                    password: document.getElementById('loginPassword').value,
                }),
            });
            const datos = await response.json();
            if (!response.ok) throw new Error(mensajeDeError(datos, 'No se pudo iniciar sesión.'));
            guardarToken(datos.token);
            if (datos.must_change_password) mostrarCambioContrasena();
            else mostrarAplicacion();
        } catch (error) {
            mostrarMensaje(error.message || 'No se pudo conectar con el servidor.');
        } finally {
            boton.disabled = false;
            document.getElementById('loginPassword').value = '';
        }
    });

    formularioCambio.addEventListener('submit', async (event) => {
        event.preventDefault();
        const boton = document.getElementById('changePasswordSubmit');
        boton.disabled = true;
        mostrarMensaje('');
        try {
            const response = await apiFetch(API_CAMBIAR_CONTRASENA, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contrasena_actual: document.getElementById('currentPassword').value,
                    nueva_contrasena: document.getElementById('newPassword').value,
                    confirmar_contrasena: document.getElementById('confirmPassword').value,
                }),
            });
            const datos = await response.json();
            if (!response.ok) throw new Error(mensajeDeError(datos, 'No se pudo cambiar la contraseña.'));
            guardarToken(datos.token);
            formularioCambio.reset();
            mostrarAplicacion();
        } catch (error) {
            mostrarMensaje(error.message || 'No se pudo conectar con el servidor.');
        } finally {
            boton.disabled = false;
        }
    });

    document.getElementById('btnLogout').addEventListener('click', async () => {
        let errorAlCerrar = false;
        try {
            await apiFetch(API_SALIDA, { method: 'POST' });
        } catch {
            errorAlCerrar = true;
        } finally {
            borrarToken();
            window.dispatchEvent(new Event('vitalair:logged-out'));
            mostrarIngreso(errorAlCerrar
                ? 'Se cerró esta sesión, pero no se pudo invalidar el token en el servidor.'
                : 'Cerraste la sesión.');
        }
    });

    window.addEventListener('vitalair:auth-expired', () => {
        mostrarIngreso('La sesión venció. Volvé a ingresar.');
    });

    async function recuperarSesion() {
        if (!obtenerToken()) {
            mostrarIngreso();
            return;
        }
        try {
            const response = await apiFetch(API_SESION);
            if (!response.ok) {
                mostrarIngreso('La sesión venció. Volvé a ingresar.');
                return;
            }
            const datos = await response.json();
            if (datos.must_change_password) mostrarCambioContrasena();
            else mostrarAplicacion();
        } catch {
            mostrarIngreso('No se pudo conectar con el servidor.');
        }
    }

    recuperarSesion();
}
