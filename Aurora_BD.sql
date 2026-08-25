-- Aurora organiza el acompañamiento prenatal; no es un expediente clínico.

create database if not exists aurora
  character set utf8mb4
  collate utf8mb4_unicode_ci;

use aurora;

set names utf8mb4;

create table if not exists roles (
  id int unsigned not null auto_increment,
  nombre varchar(50) not null,
  descripcion varchar(255) null,
  created_at timestamp not null default current_timestamp,
  primary key (id),
  unique key uk_roles_nombre (nombre)
) engine = innodb;

insert into roles (id, nombre, descripcion)
values
  (1, 'usuario', 'Consulta contenidos y administra su seguimiento prenatal.'),
  (2, 'administrador', 'Administra centros, contenidos y señales de alerta.'),
  (3, 'auditor', 'Consulta el historial de acciones administrativas.')
on duplicate key update descripcion = values(descripcion);

create table if not exists permisos (
  id int unsigned not null auto_increment,
  codigo varchar(80) not null,
  nombre varchar(120) not null,
  descripcion varchar(255) null,
  created_at timestamp not null default current_timestamp,
  primary key (id),
  unique key uk_permisos_codigo (codigo),
  unique key uk_permisos_nombre (nombre)
) engine = innodb;

insert into permisos (id, codigo, nombre, descripcion)
values
  (1, 'consultar_contenidos', 'Consultar contenidos',
    'Permite consultar información prenatal publicada.'),
  (2, 'gestionar_seguimiento', 'Gestionar seguimiento',
    'Permite administrar embarazos, controles y recordatorios propios.'),
  (3, 'consultar_centros', 'Consultar centros',
    'Permite buscar y consultar centros de atención y sus servicios.'),
  (4, 'gestionar_centros', 'Gestionar centros',
    'Permite crear, actualizar y desactivar centros y servicios.'),
  (5, 'gestionar_contenidos', 'Gestionar contenidos',
    'Permite crear, revisar y publicar contenidos prenatales.'),
  (6, 'gestionar_senales', 'Gestionar señales de alerta',
    'Permite crear, revisar y publicar señales de alerta.'),
  (7, 'consultar_auditoria', 'Consultar auditoría',
    'Permite revisar el historial de acciones administrativas.')
on duplicate key update
  nombre = values(nombre),
  descripcion = values(descripcion);

create table if not exists roles_permisos (
  rol_id int unsigned not null,
  permiso_id int unsigned not null,
  asignado_at timestamp not null default current_timestamp,
  primary key (rol_id, permiso_id),
  key idx_roles_permisos_permiso (permiso_id),
  constraint fk_roles_permisos_rol
    foreign key (rol_id)
    references roles (id)
    on delete cascade
    on update cascade,
  constraint fk_roles_permisos_permiso
    foreign key (permiso_id)
    references permisos (id)
    on delete cascade
    on update cascade
) engine = innodb;

insert into roles_permisos (rol_id, permiso_id)
values
  (1, 1),
  (1, 2),
  (1, 3),
  (2, 1),
  (2, 3),
  (2, 4),
  (2, 5),
  (2, 6),
  (3, 7)
on duplicate key update asignado_at = asignado_at;

create table if not exists centros_atencion (
  id int unsigned not null auto_increment,
  codigo_minsa varchar(20) null,
  nombre varchar(150) not null,
  tipo_establecimiento enum(
    'hospital',
    'centro_salud',
    'puesto_salud',
    'casa_materna',
    'clinica',
    'otro'
  ) not null default 'centro_salud',
  silais varchar(100) null,
  municipio varchar(100) not null,
  departamento varchar(100) not null,
  direccion text null,
  telefono varchar(30) null,
  horario varchar(255) null,
  latitud decimal(10,7) null,
  longitud decimal(10,7) null,
  fecha_verificacion date null,
  activo tinyint(1) not null default 1,
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp
    on update current_timestamp,
  primary key (id),
  unique key uk_centros_codigo_minsa (codigo_minsa),
  key idx_centros_nombre (nombre),
  key idx_centros_ubicacion (departamento, municipio),
  key idx_centros_tipo (tipo_establecimiento),
  constraint chk_centros_activo check (activo in (0, 1)),
  constraint chk_centros_latitud
    check (latitud is null or latitud between -90 and 90),
  constraint chk_centros_longitud
    check (longitud is null or longitud between -180 and 180)
) engine = innodb;

create table if not exists servicios (
  id int unsigned not null auto_increment,
  nombre varchar(120) not null,
  descripcion varchar(500) null,
  activo tinyint(1) not null default 1,
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp
    on update current_timestamp,
  primary key (id),
  unique key uk_servicios_nombre (nombre),
  key idx_servicios_activo (activo),
  constraint chk_servicios_activo check (activo in (0, 1))
) engine = innodb;

create table if not exists centros_servicios (
  centro_atencion_id int unsigned not null,
  servicio_id int unsigned not null,
  disponible tinyint(1) not null default 1,
  observaciones varchar(255) null,
  fecha_verificacion date null,
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp
    on update current_timestamp,
  primary key (centro_atencion_id, servicio_id),
  key idx_centros_servicios_servicio (servicio_id),
  key idx_centros_servicios_disponible (disponible),
  constraint fk_centros_servicios_centro
    foreign key (centro_atencion_id)
    references centros_atencion (id)
    on delete cascade
    on update cascade,
  constraint fk_centros_servicios_servicio
    foreign key (servicio_id)
    references servicios (id)
    on delete restrict
    on update cascade,
  constraint chk_centros_servicios_disponible
    check (disponible in (0, 1))
) engine = innodb;

-- Las contraseñas se almacenan exclusivamente como hash seguro.
create table if not exists usuarios (
  id int unsigned not null auto_increment,
  rol_id int unsigned not null,
  nombres varchar(100) not null,
  apellidos varchar(100) not null,
  email varchar(150) not null,
  password_hash varchar(255) not null,
  activo tinyint(1) not null default 1,
  ultimo_acceso_at datetime null,
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp
    on update current_timestamp,
  primary key (id),
  unique key uk_usuarios_email (email),
  key idx_usuarios_rol_activo (rol_id, activo),
  constraint fk_usuarios_roles
    foreign key (rol_id)
    references roles (id)
    on delete restrict
    on update cascade,
  constraint chk_usuarios_activo check (activo in (0, 1))
) engine = innodb;

create table if not exists perfiles_gestantes (
  id int unsigned not null auto_increment,
  usuario_id int unsigned not null,
  cedula varchar(20) null,
  fecha_nacimiento date null,
  telefono varchar(30) null,
  direccion_residencia text null,
  municipio varchar(100) null,
  departamento varchar(100) null,
  contacto_emergencia_nombre varchar(150) null,
  contacto_emergencia_telefono varchar(30) null,
  consentimiento_datos tinyint(1) not null default 0,
  fecha_consentimiento datetime null,
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp
    on update current_timestamp,
  primary key (id),
  unique key uk_perfiles_usuario (usuario_id),
  unique key uk_perfiles_cedula (cedula),
  constraint fk_perfiles_usuario
    foreign key (usuario_id)
    references usuarios (id)
    on delete restrict
    on update cascade,
  constraint chk_perfiles_consentimiento
    check (consentimiento_datos in (0, 1)),
  constraint chk_perfiles_fecha_consentimiento
    check (
      consentimiento_datos = 0
      or fecha_consentimiento is not null
    )
) engine = innodb;

-- FUM y FPP permiten calcular semana, trimestre y progreso sin duplicarlos.
create table if not exists embarazos (
  id int unsigned not null auto_increment,
  perfil_gestante_id int unsigned not null,
  fum date null,
  fpp date null,
  metodo_fpp enum('fum', 'ecografia', 'profesional', 'otro') null,
  estado enum('activo', 'finalizado', 'archivado')
    not null default 'activo',
  fecha_fin date null,
  notas_personales text null,
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp
    on update current_timestamp,
  primary key (id),
  key idx_embarazos_perfil_estado (perfil_gestante_id, estado),
  constraint fk_embarazos_perfil
    foreign key (perfil_gestante_id)
    references perfiles_gestantes (id)
    on delete restrict
    on update cascade,
  constraint chk_embarazos_fechas
    check (fum is not null or fpp is not null)
) engine = innodb;

-- Registra la organización del control, no información clínica.
create table if not exists controles_prenatales (
  id int unsigned not null auto_increment,
  embarazo_id int unsigned not null,
  centro_atencion_id int unsigned null,
  registrado_por_usuario_id int unsigned not null,
  numero_control smallint unsigned not null,
  fecha_control date not null,
  hora_control time null,
  edad_gestacional_semanas decimal(4,1) null,
  estado enum('programado', 'realizado', 'reprogramado', 'cancelado')
    not null default 'programado',
  indicaciones text null,
  notas text null,
  fecha_siguiente_control date null,
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp
    on update current_timestamp,
  primary key (id),
  unique key uk_controles_embarazo_numero (embarazo_id, numero_control),
  key idx_controles_fecha_estado (fecha_control, estado),
  key idx_controles_centro (centro_atencion_id),
  key idx_controles_usuario (registrado_por_usuario_id),
  constraint fk_controles_embarazo
    foreign key (embarazo_id)
    references embarazos (id)
    on delete restrict
    on update cascade,
  constraint fk_controles_centro
    foreign key (centro_atencion_id)
    references centros_atencion (id)
    on delete set null
    on update cascade,
  constraint fk_controles_usuario
    foreign key (registrado_por_usuario_id)
    references usuarios (id)
    on delete restrict
    on update cascade,
  constraint chk_controles_numero check (numero_control > 0),
  constraint chk_controles_edad_gestacional
    check (
      edad_gestacional_semanas is null
      or edad_gestacional_semanas between 0 and 45
    )
) engine = innodb;

create table if not exists recordatorios (
  id int unsigned not null auto_increment,
  usuario_id int unsigned not null,
  control_prenatal_id int unsigned null,
  titulo varchar(150) not null,
  descripcion varchar(500) null,
  tipo enum('control', 'personal', 'informativo')
    not null default 'personal',
  fecha_hora datetime not null,
  estado enum('pendiente', 'enviado', 'completado', 'cancelado')
    not null default 'pendiente',
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp
    on update current_timestamp,
  primary key (id),
  key idx_recordatorios_usuario_fecha (usuario_id, fecha_hora),
  key idx_recordatorios_estado_fecha (estado, fecha_hora),
  key idx_recordatorios_control (control_prenatal_id),
  constraint fk_recordatorios_usuario
    foreign key (usuario_id)
    references usuarios (id)
    on delete restrict
    on update cascade,
  constraint fk_recordatorios_control
    foreign key (control_prenatal_id)
    references controles_prenatales (id)
    on delete set null
    on update cascade
) engine = innodb;

create table if not exists contenidos_prenatales (
  id int unsigned not null auto_increment,
  creado_por_usuario_id int unsigned null,
  actualizado_por_usuario_id int unsigned null,
  titulo varchar(180) not null,
  resumen varchar(500) null,
  contenido longtext not null,
  categoria varchar(80) not null,
  semana_desde tinyint unsigned null,
  semana_hasta tinyint unsigned null,
  trimestre tinyint unsigned null,
  fuente_nombre varchar(180) not null,
  fuente_url varchar(500) null,
  fecha_revision date not null,
  publicado tinyint(1) not null default 0,
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp
    on update current_timestamp,
  primary key (id),
  key idx_contenidos_etapa (trimestre, semana_desde, semana_hasta),
  key idx_contenidos_categoria_publicado (categoria, publicado),
  constraint fk_contenidos_creador
    foreign key (creado_por_usuario_id)
    references usuarios (id)
    on delete set null
    on update cascade,
  constraint fk_contenidos_actualizador
    foreign key (actualizado_por_usuario_id)
    references usuarios (id)
    on delete set null
    on update cascade,
  constraint chk_contenidos_semanas
    check (
      (semana_desde is null and semana_hasta is null)
      or (
        semana_desde between 1 and 42
        and semana_hasta between semana_desde and 42
      )
    ),
  constraint chk_contenidos_trimestre
    check (trimestre is null or trimestre between 1 and 3),
  constraint chk_contenidos_publicado check (publicado in (0, 1))
) engine = innodb;

-- Cada señal conserva su fuente y fecha de revisión.
create table if not exists senales_alerta (
  id int unsigned not null auto_increment,
  creado_por_usuario_id int unsigned null,
  actualizado_por_usuario_id int unsigned null,
  titulo varchar(180) not null,
  descripcion text not null,
  accion_recomendada text not null,
  orden_visual smallint unsigned not null default 0,
  fuente_nombre varchar(180) not null,
  fuente_url varchar(500) null,
  fecha_revision date not null,
  activo tinyint(1) not null default 1,
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp
    on update current_timestamp,
  primary key (id),
  key idx_senales_activo_orden (activo, orden_visual),
  constraint fk_senales_creador
    foreign key (creado_por_usuario_id)
    references usuarios (id)
    on delete set null
    on update cascade,
  constraint fk_senales_actualizador
    foreign key (actualizado_por_usuario_id)
    references usuarios (id)
    on delete set null
    on update cascade,
  constraint chk_senales_activo check (activo in (0, 1))
) engine = innodb;

create table if not exists historial_auditoria (
  id bigint unsigned not null auto_increment,
  usuario_id int unsigned null,
  accion varchar(50) not null,
  entidad varchar(80) not null,
  registro_id bigint unsigned null,
  detalles json null,
  direccion_ip varchar(45) null,
  created_at timestamp not null default current_timestamp,
  primary key (id),
  key idx_auditoria_usuario_fecha (usuario_id, created_at),
  key idx_auditoria_entidad_registro (entidad, registro_id),
  key idx_auditoria_fecha (created_at),
  constraint fk_auditoria_usuario
    foreign key (usuario_id)
    references usuarios (id)
    on delete set null
    on update cascade
) engine = innodb;

create or replace view vista_resumen_embarazo as
select
  e.id as embarazo_id,
  pg.usuario_id,
  e.fum,
  e.fpp,
  greatest(
    0,
    least(
      42,
      floor(
        datediff(
          curdate(),
          coalesce(e.fum, date_sub(e.fpp, interval 280 day))
        ) / 7
      )
    )
  ) as semana_actual,
  CASE
    WHEN datediff(
      curdate(),
      coalesce(e.fum, date_sub(e.fpp, interval 280 day))
    ) < 14 * 7 THEN 1
    WHEN datediff(
      curdate(),
      coalesce(e.fum, date_sub(e.fpp, interval 280 day))
    ) < 28 * 7 THEN 2
    ELSE 3
  END as trimestre_actual,
  greatest(
    0,
    least(
      100,
      ROUND(
        datediff(
          curdate(),
          coalesce(e.fum, date_sub(e.fpp, interval 280 day))
        ) / 280 * 100,
        1
      )
    )
  ) as porcentaje_progreso
FROM embarazos e
inner join perfiles_gestantes pg
  on pg.id = e.perfil_gestante_id
where e.estado = 'activo';
