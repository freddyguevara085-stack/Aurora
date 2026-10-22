# Guía y Señales de alerta

## Alcance

Guía acompaña decisiones organizativas: citas, preguntas, traslado y acceso a
establecimientos. Señales de alerta muestra información educativa de fuentes
sanitarias oficiales y la acción de buscar atención. No hay cuestionarios,
diagnóstico, clasificación automática de urgencia ni indicaciones de tratamiento.

## Organización de la Guía

Los contenidos iniciales usan categorías explícitas:

| Categoría almacenada | Tema visible |
| --- | --- |
| Controles prenatales | Mis controles |
| Preparación para el parto | Prepararme para el parto |
| Acceso a la atención | Encontrar atención |

`services/exploracion.py` resuelve los temas. Mantiene compatibilidad con otras
categorías publicadas por administración: no las oculta ni elimina. Las tres
ilustraciones SVG corresponden a esos temas; son apoyos gráficos, no fotografías
de instituciones. Cada lectura conserva fuente, fecha de consulta documental y
un enlace a una acción existente de Aurora. Las fechas no acreditan validación
clínica o disponibilidad de servicios.

## Alertas

`database/seeds/senales_alerta_oficiales.json` contiene paráfrasis breves de la
cartilla del MINSA y de la campaña Hear Her de CDC, con enlaces por registro.
La acción y la descripción se leen sin abrir paneles. Solo la referencia se
pliega. El listado no es exhaustivo y no permite descartar un problema.

## Publicación y conservación

Ejecutar después de un respaldo de la base seleccionada:

```bash
python -m flask --app app consolidate-content
```

El comando confirma una transacción para los cambios editoriales y es
idempotente. Publica cuatro lecturas y nueve alertas si faltan. Reclasifica solo
las lecturas cuyo cuerpo y fuente siguen coincidiendo con el catálogo.
Retira de publicación los tres textos antiguos identificados en
`services/curacion.py` únicamente cuando título, categoría y cuerpo coinciden.
Actualiza solo el borrador respiratorio antiguo identificado explícitamente.
No borra filas ni modifica ediciones distintas de administración. No se ejecuta
en cada visita ni cambia perfiles, embarazos, contactos, citas o centros.

## Verificación antes de desplegar

- Pruebas de idempotencia y conservación de ediciones administrativas.
- Las categorías iniciales generan los tres temas previstos.
- Alertas visibles y consultables sin iniciar sesión.
- Filtros, búsqueda y lectura desplegable operativos en móvil.
- Contraste del filtro seleccionado y ausencia de desbordamiento a 320 px.
- Respaldo, publicación por CLI y comprobación del servidor desplegado.
