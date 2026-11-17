import { API_ASISTENTE, apiFetch } from './api.js';

const MAX_HISTORIAL = 10;
const historial = [];

function agregarMensaje(rol, contenido) {
    const mensaje = document.createElement('div');
    mensaje.className = `chat-message ${rol === 'user' ? 'user-message' : 'assistant-message'}`;
    mensaje.textContent = contenido;
    const mensajes = document.getElementById('chatMessages');
    mensajes.appendChild(mensaje);
    mensajes.scrollTop = mensajes.scrollHeight;
}

export function configurarChat() {
    const formulario = document.getElementById('chatForm');
    const entrada = document.getElementById('chatInput');
    const boton = document.getElementById('chatSend');

    formulario.addEventListener('submit', async (event) => {
        event.preventDefault();
        const pregunta = entrada.value.trim();
        if (!pregunta || boton.disabled) return;

        agregarMensaje('user', pregunta);
        entrada.value = '';
        entrada.disabled = true;
        boton.disabled = true;
        boton.textContent = 'Consultando...';

        try {
            const response = await apiFetch(API_ASISTENTE, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: pregunta,
                    history: historial.slice(-MAX_HISTORIAL),
                }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'No se pudo consultar al asistente.');

            agregarMensaje('assistant', data.reply);
            historial.push(
                { role: 'user', content: pregunta },
                { role: 'assistant', content: data.reply },
            );
            historial.splice(0, Math.max(0, historial.length - MAX_HISTORIAL));
        } catch (error) {
            agregarMensaje('assistant', error.message || 'No se pudo conectar con el asistente.');
        } finally {
            entrada.disabled = false;
            boton.disabled = false;
            boton.textContent = 'Enviar';
            entrada.focus();
        }
    });

    entrada.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            formulario.requestSubmit();
        }
    });
}
