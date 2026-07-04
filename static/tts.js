// =========================================================
// tts.js — Módulo de Text-to-Speech via servidor Flask
// Sistema de Votación Electrónica — Universidad de Burgos
// =========================================================

const TTS = (function () {

  let activado = true;

  // Hablar enviando el texto al servidor Flask
  async function hablar(texto, prioridad = false) {
    if (!activado || !texto) return;
    try {
      await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto })
      });
    } catch(e) {
      console.warn('[TTS] Error:', e);
    }
  }

  async function cancelar() {
    try {
      await fetch('/api/tts/cancelar', { method: 'POST' });
    } catch(e) {}
  }

  function toggle() {
    activado = !activado;
    const btn = document.getElementById('btn-tts');
    if (btn) {
      btn.innerHTML  = activado ? '🔊' : '🔇';
      btn.title      = activado ? 'Desactivar voz' : 'Activar voz';
      btn.style.opacity = activado ? '1' : '0.45';
    }
    if (activado) {
      hablar('Voz activada.');
    } else {
      cancelar();
    }
  }

  function estaActivado() { return activado; }

  return { hablar, cancelar, toggle, estaActivado };

})();


// ── Botón flotante de voz ─────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  const btn = document.createElement('button');
  btn.id        = 'btn-tts';
  btn.innerHTML = '🔊';
  btn.title     = 'Desactivar voz';
  btn.setAttribute('aria-label', 'Activar o desactivar la voz');
  btn.style.cssText = `
    position: fixed;
    bottom: 14px;
    right: 14px;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: none;
    background: #3a7abf;
    color: white;
    font-size: 20px;
    cursor: pointer;
    z-index: 9999;
    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: opacity 0.2s;
  `;
  btn.onclick = () => TTS.toggle();
  document.body.appendChild(btn);
});
