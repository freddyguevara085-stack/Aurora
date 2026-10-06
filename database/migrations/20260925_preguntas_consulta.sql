-- Aplicar una sola vez a las bases Aurora existentes antes de desplegar el código.
-- Ejecutar con la base de datos de Aurora ya seleccionada (no se fija el nombre aquí).

create table if not exists preguntas_consulta (
  id int unsigned not null auto_increment,
  usuario_id int unsigned not null,
  pregunta varchar(500) not null,
  estado enum('pendiente', 'conversada') not null default 'pendiente',
  created_at timestamp not null default current_timestamp,
  updated_at timestamp not null default current_timestamp
    on update current_timestamp,
  primary key (id),
  key idx_preguntas_usuario_estado (usuario_id, estado, id),
  constraint fk_preguntas_consulta_usuario
    foreign key (usuario_id)
    references usuarios (id)
    on delete cascade
    on update cascade,
  constraint chk_preguntas_texto check (char_length(trim(pregunta)) > 0)
) engine = innodb;
