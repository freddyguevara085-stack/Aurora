-- Migración idempotente: guarda la fecha real del nacimiento sin alterar la fecha probable de parto.
-- Nota: en instalaciones nuevas a partir de Aurora_BD.sql la columna ya forma parte de `embarazos`.
ALTER TABLE embarazos
  ADD COLUMN IF NOT EXISTS fecha_nacimiento_real DATE NULL AFTER fpp;
