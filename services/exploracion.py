"""Presentación y búsqueda de los catálogos existentes, sin servicios externos."""
from unicodedata import combining, normalize

# Categorías del catálogo inicial. Las demás conservan la compatibilidad previa.
CATEGORIAS_GUIA = {
    'controles prenatales': 'controles',
    'preparacion para el parto': 'preparacion',
    'acceso a la atencion': 'atencion',
}


def normalizar(valor):
    return ''.join(c for c in normalize('NFD', str(valor or '').lower()) if not combining(c)).strip()


def filtrar_centros(centros, departamento='', municipio='', tipo='', q=''):
    return [c for c in centros
            if (not departamento or normalizar(c.departamento) == normalizar(departamento))
            and (not municipio or normalizar(c.municipio) == normalizar(municipio))
            and (tipo in ('', 'todos') or c.tipo_establecimiento == tipo)
            and (not q or normalizar(q) in normalizar(' '.join((c.nombre, c.municipio or '', c.departamento or ''))))]


def organizar_guia(orientaciones):
    definiciones = {
        'controles': ('Mis controles', 'Fechas, consultas y seguimiento', 'event_available'),
        'preparacion': ('Prepararme para el parto', 'Organizar traslado y apoyo', 'route'),
        'atencion': ('Encontrar atención', 'Centros, acceso y cobertura', 'local_hospital'),
        'puerperio': ('Después del parto', 'Información publicada para esta etapa', 'child_friendly'),
        'registro': ('Mis documentos', 'Conocer los registros de atención', 'description'),
        'senales': ('Señales de alerta', 'Orientaciones publicadas sobre alertas', 'health_and_safety'),
        'otros': ('Cuidados y otras dudas', 'Más orientación para consultar', 'menu_book'),
    }
    cantidades = {}
    fichas = []
    for item in orientaciones:
        cat = normalizar(item['categoria'])
        if cat in CATEGORIAS_GUIA:
            grupo = CATEGORIAS_GUIA[cat]
        elif any(p in cat for p in ('puerper', 'postnat', 'postpart')):
            grupo = 'puerperio'
        elif any(p in cat for p in ('alert', 'senal', 'emerg')):
            grupo = 'senales'
        elif any(p in cat for p in ('prepar', 'parto', 'apoyo')):
            grupo = 'preparacion'
        elif any(p in cat for p in ('registr', 'document')):
            grupo = 'registro'
        elif any(p in cat for p in ('control', 'consulta', 'atencion', 'embarazo', 'exam')):
            grupo = 'controles'
        else:
            grupo = 'otros'
        cantidades[grupo] = cantidades.get(grupo, 0) + 1
        fichas.append({**item, 'tema': grupo, 'tema_titulo': definiciones[grupo][0], 'tema_icono': definiciones[grupo][2]})
    temas = [dict(id=k, titulo=v[0], descripcion=v[1], icono=v[2], cantidad=cantidades[k])
             for k, v in definiciones.items() if k in cantidades]
    return fichas, temas
