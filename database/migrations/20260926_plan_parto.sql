-- Aplicar una sola vez a las bases Aurora existentes antes de desplegar el código.
-- Ejecutar con la base de datos de Aurora ya seleccionada (no se fija el nombre aquí).

create table if not exists planes_parto (
  id int unsigned not null auto_increment,
  embarazo_id int unsigned not null,
  centro_atencion_id int unsigned null,
  requiere_casa_materna tinyint(1) not null default 0,
  acompanante_nombre varchar(150) null,
  acompanante_telefono varchar(30) null,
  cuidador_hijos varchar(150) null,
  transporte_tipo enum('propio', 'familiar_vecino', 'publico_colectivo', 'caponera_taxi', 'ambulancia_minsa', 'otro') not null default 'familiar_vecino',
  transporte_contacto varchar(150) null,
  bulto_listo tinyint(1) not null default 0,
  recursos_traslado_listos tinyint(1) not null default 0,
  notas varchar(500) null,
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp on update current_timestamp,
  primary key (id),
  unique key uk_planes_parto_embarazo (embarazo_id),
  key idx_planes_parto_centro (centro_atencion_id),
  constraint fk_planes_parto_embarazo
    foreign key (embarazo_id)
    references embarazos (id)
    on delete cascade
    on update cascade,
  constraint fk_planes_parto_centro
    foreign key (centro_atencion_id)
    references centros_atencion (id)
    on delete set null
    on update cascade,
  constraint chk_planes_parto_casa check (requiere_casa_materna in (0, 1)),
  constraint chk_planes_parto_bulto check (bulto_listo in (0, 1)),
  constraint chk_planes_parto_recursos check (recursos_traslado_listos in (0, 1))
) engine = innodb;
