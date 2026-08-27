-- Datos iniciales idempotentes del MVP Aurora.
-- Fuentes de orientación: OPS/OMS, Salud materna,
-- https://www.paho.org/es/temas/salud-materna (revisada el 2026-08-27).
-- No modifica usuarios, centros ni datos clínicos personales.

INSERT INTO servicios (nombre, descripcion, activo)
SELECT 'Atención prenatal', 'Seguimiento general durante el embarazo.' , 1
WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'Atención prenatal');

INSERT INTO servicios (nombre, descripcion, activo)
SELECT 'Planificación familiar', 'Orientación general sobre salud sexual y reproductiva.', 1
WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'Planificación familiar');

INSERT INTO servicios (nombre, descripcion, activo)
SELECT 'Vacunación', 'Atención para esquemas de vacunación según indicación profesional.', 1
WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'Vacunación');

INSERT INTO servicios (nombre, descripcion, activo)
SELECT 'Atención materna y neonatal', 'Orientación y atención para salud materna y del recién nacido.', 1
WHERE NOT EXISTS (SELECT 1 FROM servicios WHERE nombre = 'Atención materna y neonatal');

INSERT INTO contenidos_prenatales
    (creado_por_usuario_id, actualizado_por_usuario_id, titulo, resumen, contenido, categoria,
     semana_desde, semana_hasta, trimestre, fuente_nombre, fuente_url, fecha_revision, publicado)
SELECT NULL, NULL,
       'Primer trimestre: organiza tu atención prenatal',
       'Una guía breve para preparar preguntas y mantener tus controles al día.',
       'La atención prenatal ayuda a acompañar el embarazo con el equipo de salud. Puedes anotar preguntas, compartir cambios que te preocupen y asistir a los controles indicados. Esta información es educativa y no sustituye la orientación profesional.',
       'atención prenatal', 1, 13, 1,
       'OPS/OMS - Salud materna', 'https://www.paho.org/es/temas/salud-materna', '2026-08-27', 1
WHERE NOT EXISTS (SELECT 1 FROM contenidos_prenatales WHERE titulo = 'Primer trimestre: organiza tu atención prenatal');

INSERT INTO contenidos_prenatales
    (creado_por_usuario_id, actualizado_por_usuario_id, titulo, resumen, contenido, categoria,
     semana_desde, semana_hasta, trimestre, fuente_nombre, fuente_url, fecha_revision, publicado)
SELECT NULL, NULL,
       'Segundo trimestre: continúa el acompañamiento',
       'Mantén una comunicación clara con el personal de salud durante tus controles.',
       'El segundo trimestre puede ser un buen momento para revisar tus próximas citas y conversar con el equipo de salud sobre tus necesidades. Busca orientación profesional para cualquier duda o cambio relacionado con tu embarazo.',
       'bienestar', 14, 27, 2,
       'OPS/OMS - Salud materna', 'https://www.paho.org/es/temas/salud-materna', '2026-08-27', 1
WHERE NOT EXISTS (SELECT 1 FROM contenidos_prenatales WHERE titulo = 'Segundo trimestre: continúa el acompañamiento');

INSERT INTO contenidos_prenatales
    (creado_por_usuario_id, actualizado_por_usuario_id, titulo, resumen, contenido, categoria,
     semana_desde, semana_hasta, trimestre, fuente_nombre, fuente_url, fecha_revision, publicado)
SELECT NULL, NULL,
       'Tercer trimestre: prepara tu red de apoyo',
       'Planifica cómo contactar a tu red de apoyo y a los servicios de salud cuando lo necesites.',
       'Durante el tercer trimestre, conversar sobre transporte, acompañamiento y contactos de atención puede facilitar la organización. Sigue las indicaciones de tu equipo de salud y consulta si aparece algo que te preocupe.',
       'preparación', 28, 42, 3,
       'OPS/OMS - Salud materna', 'https://www.paho.org/es/temas/salud-materna', '2026-08-27', 1
WHERE NOT EXISTS (SELECT 1 FROM contenidos_prenatales WHERE titulo = 'Tercer trimestre: prepara tu red de apoyo');

INSERT INTO senales_alerta
    (creado_por_usuario_id, actualizado_por_usuario_id, titulo, descripcion, accion_recomendada,
     orden_visual, fuente_nombre, fuente_url, fecha_revision, activo)
SELECT NULL, NULL, 'Sangrado vaginal',
       'El sangrado durante el embarazo merece una valoración profesional.',
       'Busca atención profesional de inmediato.', 1,
       'OPS/OMS - Salud materna', 'https://www.paho.org/es/temas/salud-materna', '2026-08-27', 1
WHERE NOT EXISTS (SELECT 1 FROM senales_alerta WHERE titulo = 'Sangrado vaginal');

INSERT INTO senales_alerta
    (creado_por_usuario_id, actualizado_por_usuario_id, titulo, descripcion, accion_recomendada,
     orden_visual, fuente_nombre, fuente_url, fecha_revision, activo)
SELECT NULL, NULL, 'Fiebre o escalofríos',
       'La fiebre o los escalofríos pueden requerir una valoración oportuna.',
       'Busca atención profesional lo antes posible.', 2,
       'OPS/OMS - Salud materna', 'https://www.paho.org/es/temas/salud-materna', '2026-08-27', 1
WHERE NOT EXISTS (SELECT 1 FROM senales_alerta WHERE titulo = 'Fiebre o escalofríos');

INSERT INTO senales_alerta
    (creado_por_usuario_id, actualizado_por_usuario_id, titulo, descripcion, accion_recomendada,
     orden_visual, fuente_nombre, fuente_url, fecha_revision, activo)
SELECT NULL, NULL, 'Dolor intenso o persistente',
       'Un dolor intenso o que no mejora necesita orientación profesional.',
       'Busca atención profesional de inmediato.', 3,
       'OPS/OMS - Salud materna', 'https://www.paho.org/es/temas/salud-materna', '2026-08-27', 1
WHERE NOT EXISTS (SELECT 1 FROM senales_alerta WHERE titulo = 'Dolor intenso o persistente');

INSERT INTO senales_alerta
    (creado_por_usuario_id, actualizado_por_usuario_id, titulo, descripcion, accion_recomendada,
     orden_visual, fuente_nombre, fuente_url, fecha_revision, activo)
SELECT NULL, NULL, 'Dificultad para respirar o dolor en el pecho',
       'La dificultad para respirar o el dolor en el pecho requieren atención urgente.',
       'Busca atención profesional de inmediato o utiliza los servicios de emergencia disponibles.', 4,
       'OPS/OMS - Salud materna', 'https://www.paho.org/es/temas/salud-materna', '2026-08-27', 1
WHERE NOT EXISTS (SELECT 1 FROM senales_alerta WHERE titulo = 'Dificultad para respirar o dolor en el pecho');

INSERT INTO senales_alerta
    (creado_por_usuario_id, actualizado_por_usuario_id, titulo, descripcion, accion_recomendada,
     orden_visual, fuente_nombre, fuente_url, fecha_revision, activo)
SELECT NULL, NULL, 'Cambios que te preocupen',
       'Si notas un cambio que te preocupa, es importante solicitar orientación.',
       'Comunícate con un profesional de salud para recibir orientación.', 5,
       'OPS/OMS - Salud materna', 'https://www.paho.org/es/temas/salud-materna', '2026-08-27', 1
WHERE NOT EXISTS (SELECT 1 FROM senales_alerta WHERE titulo = 'Cambios que te preocupen');
