if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then(() => console.log('Service worker registrado'))
      .catch(err => console.log('Error registrando service worker', err));
  });
}

function prepararPreferenciasPerfil() {
  const niveles = ['normal', 'grande'];
  const boton = document.querySelector('[data-aurora-font-size]');
  const etiqueta = document.querySelector('[data-aurora-font-label]');
  let nivel = localStorage.getItem('aurora-font-size') || 'normal';
  const aplicarNivel = () => {
    document.body.classList.toggle('text-large', nivel === 'grande');
    if (etiqueta) etiqueta.textContent = nivel === 'grande' ? 'Grande' : 'Normal';
  };
  aplicarNivel();
  if (boton) {
    boton.addEventListener('click', () => {
      nivel = niveles[(niveles.indexOf(nivel) + 1) % niveles.length];
      localStorage.setItem('aurora-font-size', nivel);
      aplicarNivel();
    });
  }
}

window.addEventListener('load', () => {
  prepararPreferenciasPerfil();
});
