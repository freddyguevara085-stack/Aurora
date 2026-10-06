const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('static/js/app.js', 'utf8');

function montarAurora({ conBoton = true } = {}) {
  const eventos = {};
  const handlers = {};
  let impresiones = 0;
  const boton = { addEventListener: (_, handler) => { handlers.print = handler; } };
  const window = {
    addEventListener: (name, handler) => { eventos[name] = handler; },
    print: () => { impresiones += 1; },
  };
  const document = {
    body: { classList: { toggle() {} } },
    addEventListener() {},
    querySelector: selector => (conBoton && selector === '[data-print-action]' ? boton : null),
    getElementById: () => null,
    querySelectorAll: () => [],
  };
  const storage = { getItem: () => null, setItem() {}, removeItem() {} };

  vm.runInNewContext(source, {
    window,
    document,
    navigator: {},
    localStorage: storage,
    sessionStorage: storage,
  });
  eventos.load();
  return { boton, eventos, handlers, impresiones: () => impresiones };
}

test('abre el diálogo nativo solo tras el clic del botón', () => {
  const app = montarAurora();

  assert.equal(app.impresiones(), 0);
  assert.equal(typeof app.handlers.print, 'function');
  app.handlers.print();
  assert.equal(app.impresiones(), 1);
});

test('sin botón de impresión no dispara el diálogo', () => {
  const app = montarAurora({ conBoton: false });

  assert.equal(app.handlers.print, undefined);
  assert.equal(app.impresiones(), 0);
});
