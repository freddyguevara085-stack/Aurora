-- Aplicar una sola vez a las bases Aurora existentes antes de desplegar el código.
-- Ejecutar con la base de datos de Aurora ya seleccionada (no se fija el nombre aquí).

create table if not exists contactos_comunitarios (
  id int unsigned not null auto_increment,
  perfil_gestante_id int unsigned not null,
  nombre varchar(150) not null,
  rol enum('brigadista', 'partera', 'promotor_salud', 'traslado_local', 'lider_comunitario', 'vecino_apoyo', 'otro') not null default 'brigadista',
  telefono varchar(30) null,
  comunidad_barrio varchar(150) null,
  notas varchar(255) null,
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp on update current_timestamp,
  primary key (id),
  key idx_contactos_perfil (perfil_gestante_id),
  key idx_contactos_rol (rol),
  constraint fk_contactos_perfil
    foreign key (perfil_gestante_id)
    references perfiles_gestantes (id)
    on delete cascade
    on update cascade
) engine = innodb;
