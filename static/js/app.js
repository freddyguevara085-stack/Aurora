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

function prepararCompartirConsulta() {
  const tarjeta = document.querySelector('[data-appointment-share]');
  if (!tarjeta) return;

  const compartir = tarjeta.querySelector('[data-share-action]');
  const copiar = tarjeta.querySelector('[data-copy-action]');
  const estado = tarjeta.querySelector('[data-share-status]');
  const { shareDate, shareTime, shareCenter } = tarjeta.dataset;
  const texto = `Fecha: ${shareDate}\nHora: ${shareTime}\nCentro: ${shareCenter}`;

  if (typeof navigator.share === 'function') {
    compartir.hidden = false;
    compartir.addEventListener('click', async () => {
      try {
        await navigator.share({ title: 'Datos de mi próxima consulta', text: texto });
        estado.textContent = 'Se compartieron los datos logísticos de la consulta.';
      } catch (error) {
        estado.textContent = error?.name === 'AbortError'
          ? 'No se compartió la cita. Puedes consultar o seleccionar los datos logísticos.'
          : 'No se pudo compartir. Puedes consultar o seleccionar los datos logísticos.';
      }
    });
  }

  if (typeof navigator.clipboard?.writeText === 'function') {
    copiar.hidden = false;
    copiar.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(texto);
        estado.textContent = 'Se copiaron los datos logísticos de la consulta.';
      } catch (_error) {
        estado.textContent = 'No se pudo copiar. Puedes seleccionar los datos logísticos para copiarlos manualmente.';
      }
    });
  }
}

function prepararInstalacion() {
  const aviso = document.querySelector('[data-install-banner]');
  if (!aviso || sessionStorage.getItem('aurora-install-dismissed') === '1') return;

  const botonInstalar = aviso.querySelector('[data-install-action]');
  const botonCerrar = aviso.querySelector('[data-install-dismiss]');
  const estado = aviso.querySelector('[data-install-status]');
  let instalacion;

  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    instalacion = event;
    aviso.hidden = false;
  });

  botonInstalar.addEventListener('click', async () => {
    if (!instalacion) return;
    botonInstalar.disabled = true;
    try {
      instalacion.prompt();
      const { outcome } = await instalacion.userChoice;
      estado.textContent = outcome === 'accepted'
        ? 'Aurora se está instalando en tu dispositivo.'
        : 'No se instaló. Puedes hacerlo luego desde el menú del navegador.';
      if (outcome !== 'accepted') sessionStorage.setItem('aurora-install-dismissed', '1');
      aviso.hidden = true;
      instalacion = null;
    } catch (_error) {
      estado.textContent = 'No se pudo iniciar la instalación. Puedes usar el menú del navegador.';
      aviso.hidden = true;
      sessionStorage.setItem('aurora-install-dismissed', '1');
    } finally {
      botonInstalar.disabled = false;
    }
  });

  botonCerrar.addEventListener('click', () => {
    aviso.hidden = true;
    sessionStorage.setItem('aurora-install-dismissed', '1');
  });

  window.addEventListener('appinstalled', () => {
    aviso.hidden = true;
    sessionStorage.removeItem('aurora-install-dismissed');
    estado.textContent = 'Aurora quedó instalada en tu dispositivo.';
  });
}

function prepararImpresionConsulta() {
  const boton = document.querySelector('[data-print-action]');
  if (!boton) return;
  boton.addEventListener('click', () => window.print());
}

function prepararConfirmaciones() {
  const dialog = document.getElementById('aurora-confirm');
  if (!dialog) return;
  const mensaje = dialog.querySelector('[data-confirm-message]');
  const botonOk = dialog.querySelector('[data-confirm-ok]');
  const botonCancelar = dialog.querySelector('[data-confirm-cancel]');
  let formPendiente = null;

  document.querySelectorAll('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', event => {
      if (form.dataset.confirmado === '1') {
        delete form.dataset.confirmado;
        return;
      }
      event.preventDefault();
      formPendiente = form;
      mensaje.textContent = form.dataset.confirm;
      botonOk.textContent = form.dataset.confirmOk || 'Eliminar';
      if (typeof dialog.showModal === 'function') {
        dialog.showModal();
        botonCancelar.focus();
      } else if (window.confirm(form.dataset.confirm)) {
        form.dataset.confirmado = '1';
        form.requestSubmit();
      }
    });
  });

  botonCancelar.addEventListener('click', () => dialog.close());
  botonOk.addEventListener('click', () => {
    const form = formPendiente;
    dialog.close();
    if (form) {
      form.dataset.confirmado = '1';
      form.requestSubmit();
    }
  });
  dialog.addEventListener('close', () => {
    formPendiente = null;
  });
}

// Un único listener delegado para todos los <form method="post">: muestra el
// botón en "Guardando…" mientras la página responde. Se excluyen los forms con
// data-no-loading y cualquier form dentro del diálogo #aurora-confirm.
function prepararEnvioDeFormularios() {
  document.addEventListener('submit', event => {
    if (event.defaultPrevented) return;
    const form = event.target;
    if (!form || form.tagName !== 'FORM' || form.method !== 'post') return;
    if (form.hasAttribute('data-no-loading') || form.closest('#aurora-confirm')) return;
    const boton = form.querySelector('button[type="submit"], button:not([type])');
    if (!boton || boton.disabled) return;
    boton.dataset.idleHtml = boton.innerHTML;
    boton.textContent = 'Guardando…';
    boton.setAttribute('aria-busy', 'true');
    boton.disabled = true;
  });
}

// Al volver con el botón Atrás, algunos navegadores restauran la página desde
// bfcache con el botón de envío aún deshabilitado. Se reactiva para poder
// reenviar sin recargar manualmente.
function prepararRecuperacionDeFormularios() {
  window.addEventListener('pageshow', event => {
    if (!event.persisted) return;
    document.querySelectorAll('button[aria-busy="true"]').forEach(boton => {
      if (boton.dataset.idleHtml) boton.innerHTML = boton.dataset.idleHtml;
      boton.disabled = false;
      boton.removeAttribute('aria-busy');
    });
  });
}

// Al pulsar un enlace de la barra inferior se programa un skeleton tras 300 ms;
// si la página llega antes, la navegación lo descarta y no se ve. Sin JS nada
// de esto ocurre y la navegación es la de siempre.
function prepararSkeletonNavegacion() {
  let temporizador = null;
  const limpiar = () => {
    clearTimeout(temporizador);
    temporizador = null;
    document.querySelectorAll('.skeleton').forEach(s => s.remove());
    const main = document.getElementById('main');
    if (main) main.removeAttribute('aria-busy');
  };
  document.addEventListener('click', event => {
    if (event.defaultPrevented || event.button !== 0) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const enlace = event.target.closest('.bottom-nav a[href]');
    if (!enlace || enlace.target) return;
    if (new URL(enlace.href, location.href).origin !== location.origin) return;
    temporizador = setTimeout(() => {
      const main = document.getElementById('main');
      if (!main) return;
      const esqueleto = document.createElement('div');
      esqueleto.className = 'skeleton';
      esqueleto.setAttribute('aria-hidden', 'true');
      esqueleto.innerHTML = '<span class="skeleton__bar"></span><span class="skeleton__card"></span><span class="skeleton__card"></span>';
      main.appendChild(esqueleto);
      main.setAttribute('aria-busy', 'true');
    }, 300);
  });
  window.addEventListener('pageshow', limpiar);
}

function prepararGuiaInicial() {
  const dialogo = document.querySelector('[data-aurora-tutorial]');
  if (!dialogo) return;

  const pasos = [
    ['Bienvenida a Aurora', 'Organiza la información de tu embarazo, tus controles y tus preguntas para la atención prenatal.'],
    ['Registra lo que ya sabes', 'Puedes indicar la FUM, la fecha probable de parto o las semanas que te informó un profesional.'],
    ['Tu semana avanza automáticamente', 'Aurora calcula la semana con tus fechas. Si no coincide, puedes corregirlas desde “Mi embarazo”.'],
  ];
  const titulo = dialogo.querySelector('[data-guide-title]');
  const copia = dialogo.querySelector('[data-guide-copy]');
  const etiqueta = dialogo.querySelector('[data-guide-step]');
  const progreso = dialogo.querySelector('[data-guide-progress]');
  const anterior = dialogo.querySelector('[data-guide-back]');
  const siguiente = dialogo.querySelector('[data-guide-next]');
  const clave = `aurora-guia-v1-${dialogo.dataset.userId}`;
  let paso = 0;

  const renderizarPaso = () => {
    [titulo.textContent, copia.textContent] = pasos[paso];
    etiqueta.textContent = `Paso ${paso + 1} de ${pasos.length}`;
    progreso.value = paso + 1;
    progreso.setAttribute('aria-label', etiqueta.textContent);
    anterior.hidden = paso === 0;
    siguiente.textContent = paso === pasos.length - 1 ? 'Empezar' : 'Continuar';
  };
  const abrir = () => {
    paso = 0;
    renderizarPaso();
    dialogo.showModal();
  };

  dialogo.querySelectorAll('[data-guide-skip]').forEach(boton => boton.addEventListener('click', () => dialogo.close()));
  anterior.addEventListener('click', () => { paso -= 1; renderizarPaso(); });
  siguiente.addEventListener('click', () => {
    if (paso === pasos.length - 1) dialogo.close();
    else { paso += 1; renderizarPaso(); }
  });
  dialogo.addEventListener('close', () => {
    try { localStorage.setItem(clave, 'visto'); } catch {}
  });
  document.querySelector('[data-guide-open]')?.addEventListener('click', abrir);
  try {
    if (localStorage.getItem(clave) !== 'visto') abrir();
  } catch {
    // El acceso manual sigue disponible si el navegador bloquea el almacenamiento local.
  }
}

// Guía prenatal / Orientación: acordeón accesible y filtrado reactivo
function prepararOrientacion() {
  const contenedor = document.getElementById('orient-list');
  if (!contenedor) return;

  const searchInput = document.getElementById('orient-q');
  const chips = document.querySelectorAll('.orient-chip[data-filter]');
  const cards = contenedor.querySelectorAll('.orient-card');
  const noResults = document.getElementById('orient-no-results');
  const resetBtn = document.getElementById('orient-reset-btn');
  const liveRegion = document.getElementById('orient-live-region');
  const userTrimestre = contenedor.dataset.userTrimestre || '';

  let filtroActivo = 'todas';
  let queryBusqueda = '';

  function normalizarTexto(txt) {
    return (txt || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .trim();
  }

  function coincideCategoria(card, filtro) {
    if (filtro === 'todas') return true;
    if (filtro === 'mi-trimestre') {
      if (!userTrimestre) return true;
      const cardTrimestre = card.dataset.trimestre;
      return !cardTrimestre || cardTrimestre === userTrimestre;
    }
    const cat = normalizarTexto(card.dataset.cat);
    const searchData = normalizarTexto(card.dataset.search);
    if (filtro === 'alimentacion') {
      return cat.includes('aliment') || cat.includes('cuid') || cat.includes('nutri') || cat.includes('bienestar') || searchData.includes('nutricion') || searchData.includes('dieta');
    }
    if (filtro === 'senales') {
      return cat.includes('alerta') || cat.includes('emerg') || cat.includes('sintoma') || cat.includes('peligro') || searchData.includes('hemorragia') || searchData.includes('preeclampsia') || searchData.includes('infeccion');
    }
    if (filtro === 'controles') {
      return cat.includes('control') || cat.includes('consult') || cat.includes('exam') || cat.includes('atencion') || cat.includes('tramite') || searchData.includes('control');
    }
    if (filtro === 'preparacion') {
      return cat.includes('prepar') || cat.includes('parto') || cat.includes('apoyo') || cat.includes('red') || cat.includes('prevencion') || searchData.includes('parto') || searchData.includes('adolescencia');
    }
    return cat.includes(filtro);
  }

  function aplicarFiltros() {
    const q = normalizarTexto(queryBusqueda);
    let visibles = 0;

    cards.forEach(card => {
      const matchCat = coincideCategoria(card, filtroActivo);
      const matchSearch = !q || normalizarTexto(card.dataset.search).includes(q);
      const visible = matchCat && matchSearch;

      if (visible) {
        card.removeAttribute('hidden');
        visibles++;
      } else {
        card.setAttribute('hidden', '');
      }
    });

    if (noResults) {
      if (cards.length > 0 && visibles === 0) {
        noResults.removeAttribute('hidden');
      } else {
        noResults.setAttribute('hidden', '');
      }
    }

    if (liveRegion && cards.length > 0) {
      if (visibles === 0) {
        liveRegion.textContent = 'No se encontraron orientaciones para este filtro.';
      } else if (visibles === 1) {
        liveRegion.textContent = '1 orientación disponible.';
      } else {
        liveRegion.textContent = `${visibles} orientaciones disponibles.`;
      }
    }
  }

  // Alterna el chip activo y expone el estado a lectores de pantalla
  function activarChip(activo) {
    chips.forEach(c => {
      const on = c === activo;
      c.classList.toggle('is-active', on);
      c.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }

  // Chips click
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      activarChip(chip);
      filtroActivo = chip.dataset.filter;
      aplicarFiltros();
    });
  });

  // Búsqueda instantánea en cliente
  if (searchInput) {
    searchInput.addEventListener('input', e => {
      queryBusqueda = e.target.value;
      aplicarFiltros();
    });
  }

  // Botón restablecer búsqueda
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      if (searchInput) {
        searchInput.value = '';
        queryBusqueda = '';
      }
      filtroActivo = 'todas';
      activarChip(Array.from(chips).find(c => c.dataset.filter === 'todas'));
      aplicarFiltros();
      if (searchInput) {
        searchInput.focus();
      }
    });
  }

  // Lectura de parámetros URL iniciales (ej. /guia?filtro=senales o ?q=cuidado)
  try {
    const params = new URLSearchParams(window.location.search);
    const paramFiltro = params.get('filtro');
    const paramQ = params.get('q');

    if (paramQ && searchInput) {
      searchInput.value = paramQ;
      queryBusqueda = paramQ;
    }

    if (paramFiltro) {
      const chipMatch = Array.from(chips).find(c => c.dataset.filter === paramFiltro);
      if (chipMatch) {
        activarChip(chipMatch);
        filtroActivo = paramFiltro;
      }
    }

    if (paramQ || (paramFiltro && paramFiltro !== 'todas')) {
      aplicarFiltros();
    }
  } catch (_e) {
    // Si la plataforma no soporta URLSearchParams, continúa con valores por defecto
  }

  // Acordeón / tarjetas expandibles
  cards.forEach((card, index) => {
    const toggle = card.querySelector('.orient-card__toggle');
    const body = card.querySelector('.orient-card__body');
    if (!toggle || !body) return;

    const id = body.id || `orient-body-${index}`;
    body.id = id;
    toggle.setAttribute('aria-controls', id);

    toggle.addEventListener('click', () => {
      const expandido = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!expandido));
      card.setAttribute('aria-expanded', String(!expandido));
      body.hidden = expandido;
    });
  });
}

// Directorio de centros de salud: búsqueda reactiva y filtrado combinado
function prepararDirectorioCentros() {
  const contenedor = document.getElementById('centros-list');
  if (!contenedor) return;

  const searchInput = document.getElementById('centros-q');
  const deptoSelect = document.getElementById('centros-depto');
  const chips = document.querySelectorAll('.centros-chips [data-tipo]');
  const cards = contenedor.querySelectorAll('.centro-card');
  const noResults = document.getElementById('centros-no-results');
  const resetBtn = document.getElementById('centros-reset-btn');
  const liveRegion = document.getElementById('centros-live-region');

  let filtroTipo = 'todos';
  let filtroDepto = deptoSelect ? deptoSelect.value : '';
  let queryBusqueda = searchInput ? searchInput.value : '';

  function normalizar(txt) {
    return (txt || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .trim();
  }

  function aplicarFiltros() {
    const q = normalizar(queryBusqueda);
    const deptoTarget = normalizar(filtroDepto);
    let visibles = 0;

    cards.forEach(card => {
      const nombre = normalizar(card.dataset.nombre);
      const municipio = normalizar(card.dataset.municipio);
      const departamento = normalizar(card.dataset.departamento);
      const tipo = card.dataset.tipo;

      const matchSearch = !q || nombre.includes(q) || municipio.includes(q) || departamento.includes(q);
      const matchDepto = !deptoTarget || departamento === deptoTarget;
      const matchTipo = filtroTipo === 'todos' || tipo === filtroTipo;

      const visible = matchSearch && matchDepto && matchTipo;

      if (visible) {
        card.removeAttribute('hidden');
        visibles++;
      } else {
        card.setAttribute('hidden', '');
      }
    });

    if (noResults) {
      if (cards.length > 0 && visibles === 0) {
        noResults.removeAttribute('hidden');
      } else {
        noResults.setAttribute('hidden', '');
      }
    }

    if (liveRegion && cards.length > 0) {
      if (visibles === 0) {
        liveRegion.textContent = 'No se encontraron centros de salud con estos filtros.';
      } else if (visibles === 1) {
        liveRegion.textContent = '1 centro de salud encontrado.';
      } else {
        liveRegion.textContent = `Mostrando ${visibles} centros de salud.`;
      }
    }
  }

  // Alterna el chip de tipo activo y expone el estado a lectores de pantalla
  function activarChipTipo(activo) {
    chips.forEach(c => {
      const on = c === activo;
      c.classList.toggle('is-active', on);
      c.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }

  // Chips de tipo
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      activarChipTipo(chip);
      filtroTipo = chip.dataset.tipo;
      aplicarFiltros();
    });
  });

  // Selector de departamento
  if (deptoSelect) {
    deptoSelect.addEventListener('change', () => {
      filtroDepto = deptoSelect.value;
      aplicarFiltros();
    });
  }

  // Búsqueda en tiempo real
  if (searchInput) {
    searchInput.addEventListener('input', e => {
      queryBusqueda = e.target.value;
      aplicarFiltros();
    });
  }

  // Botón restablecer filtros
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      if (searchInput) {
        searchInput.value = '';
        queryBusqueda = '';
      }
      if (deptoSelect) {
        deptoSelect.value = '';
        filtroDepto = '';
      }
      filtroTipo = 'todos';
      activarChipTipo(Array.from(chips).find(c => c.dataset.tipo === 'todos'));
      aplicarFiltros();
      if (searchInput) {
        searchInput.focus();
      }
    });
  }

  // Deep linking desde URL (?departamento=..., ?tipo=..., ?q=...)
  try {
    const params = new URLSearchParams(window.location.search);
    const paramQ = params.get('q');
    const paramTipo = params.get('tipo');
    const paramDepto = params.get('departamento');

    if (paramQ && searchInput) {
      searchInput.value = paramQ;
      queryBusqueda = paramQ;
    }

    if (paramTipo) {
      const matchingChip = Array.from(chips).find(c => c.dataset.tipo === paramTipo);
      if (matchingChip) {
        activarChipTipo(matchingChip);
        filtroTipo = paramTipo;
      }
    }

    if (paramDepto && deptoSelect) {
      deptoSelect.value = paramDepto;
      filtroDepto = paramDepto;
    }

    if (paramQ || (paramTipo && paramTipo !== 'todos') || paramDepto || (deptoSelect && deptoSelect.value)) {
      aplicarFiltros();
    }
  } catch (_e) {
    // Continuar si la plataforma no soporta URLSearchParams
  }
}

function prepararToasts() {
  const mensajes = document.querySelectorAll('.flash');
  if (!mensajes.length) return;
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.setAttribute('role', 'status');
  toast.setAttribute('aria-live', 'polite');
  mensajes.forEach(mensaje => {
    mensaje.removeAttribute('role');
    toast.appendChild(mensaje);
  });
  const cerrar = () => toast.remove();
  const boton = document.createElement('button');
  boton.type = 'button';
  boton.className = 'toast__close';
  boton.setAttribute('aria-label', 'Cerrar aviso');
  boton.textContent = '×';
  boton.addEventListener('click', cerrar);
  toast.appendChild(boton);
  document.body.appendChild(toast);
  const tieneError = Array.from(mensajes).some(m => m.classList.contains('flash--error'));
  if (!tieneError) setTimeout(cerrar, 4000);
}

window.addEventListener('load', () => {
  prepararPreferenciasPerfil();
  prepararToasts();
  prepararCompartirConsulta();
  prepararInstalacion();
  prepararImpresionConsulta();
  prepararConfirmaciones();
  prepararEnvioDeFormularios();
  prepararRecuperacionDeFormularios();
  prepararSkeletonNavegacion();
  prepararGuiaInicial();
  prepararOrientacion();
  prepararDirectorioCentros();
});
