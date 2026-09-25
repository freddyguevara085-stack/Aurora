const AURORA_ICON = '/static/assets/inicio/aurora-logo.png';

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then(() => console.log('Service worker registrado'))
      .catch(err => console.log('Error registrando service worker', err));
  });
}

function notificacionesSoportadas() {
  return 'Notification' in window;
}

function avisosDeHoy() {
  const nodo = document.getElementById('aurora-avisos');
  if (!nodo) return [];
  try {
    return JSON.parse(nodo.textContent || '[]');
  } catch (err) {
    return [];
  }
}

function mostrarAvisosDeHoy() {
  if (!notificacionesSoportadas() || Notification.permission !== 'granted') return;
  avisosDeHoy().forEach(aviso => {
    try {
      if (sessionStorage.getItem(`aurora-aviso-${aviso.id}`)) return;
      sessionStorage.setItem(`aurora-aviso-${aviso.id}`, '1');
    } catch (err) {
      // sessionStorage puede no estar disponible; se notifica igual.
    }
    new Notification(aviso.titulo, {
      body: aviso.detalle || 'Recordatorio de Aurora',
      icon: AURORA_ICON,
    });
  });
}

function solicitarPermisoNotificaciones() {
  if (!notificacionesSoportadas()) return;
  Notification.requestPermission().then(permiso => {
    if (permiso === 'granted') {
      document.querySelectorAll('[data-aurora-notify]').forEach(boton => { boton.hidden = true; });
      mostrarAvisosDeHoy();
    }
  });
}

function prepararNotificaciones() {
  const botones = document.querySelectorAll('[data-aurora-notify]');
  botones.forEach(boton => {
    if (!notificacionesSoportadas() || Notification.permission === 'granted') {
      boton.hidden = true;
      return;
    }
    boton.addEventListener('click', solicitarPermisoNotificaciones);
  });
  mostrarAvisosDeHoy();
}

window.addEventListener('load', prepararNotificaciones);
