const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('static/js/app.js', 'utf8');

function montarAurora() {
  const eventos = {};
  const handlers = {};
  const sesion = new Map();
  const controles = {
    '[data-install-action]': { addEventListener: (_, handler) => { handlers.install = handler; } },
    '[data-install-dismiss]': { addEventListener: (_, handler) => { handlers.dismiss = handler; } },
    '[data-install-status]': { textContent: '' },
  };
  const aviso = {
    hidden: true,
    querySelector: selector => controles[selector],
  };
  const window = { addEventListener: (name, handler) => { eventos[name] = handler; } };
  const document = {
    body: { classList: { toggle() {} } },
    addEventListener() {},
    querySelector: selector => selector === '[data-install-banner]' ? aviso : null,
    getElementById: () => null,
    querySelectorAll: () => [],
  };
  const storage = {
    getItem: key => sesion.get(key) || null,
    setItem: (key, value) => sesion.set(key, value),
    removeItem: key => sesion.delete(key),
  };

  vm.runInNewContext(source, {
    window,
    document,
    navigator: {},
    localStorage: storage,
    sessionStorage: storage,
  });
  eventos.load();
  return { aviso, controles, eventos, handlers, sesion };
}

test('muestra el aviso solo tras el evento e inicia la instalación bajo demanda', async () => {
  const app = montarAurora();
  let prevenido = false;
  let prompts = 0;
  app.eventos.beforeinstallprompt({
    preventDefault: () => { prevenido = true; },
    prompt: () => { prompts += 1; },
    userChoice: Promise.resolve({ outcome: 'accepted' }),
  });

  assert.equal(prevenido, true);
  assert.equal(app.aviso.hidden, false);
  assert.equal(prompts, 0);
  await app.handlers.install();
  assert.equal(prompts, 1);
  assert.equal(app.aviso.hidden, true);
  assert.match(app.controles['[data-install-status]'].textContent, /se está instalando/);
});

test('permite descartar el aviso por el resto de la sesión', () => {
  const app = montarAurora();
  app.eventos.beforeinstallprompt({ preventDefault() {}, prompt() {}, userChoice: Promise.resolve({ outcome: 'dismissed' }) });
  app.handlers.dismiss();

  assert.equal(app.aviso.hidden, true);
  assert.equal(app.sesion.get('aurora-install-dismissed'), '1');
});
