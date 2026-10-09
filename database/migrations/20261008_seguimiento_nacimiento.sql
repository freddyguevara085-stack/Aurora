-- Guarda la fecha real del nacimiento sin alterar la fecha probable de parto.
ALTER TABLE embarazos
  ADD COLUMN fecha_nacimiento_real DATE NULL AFTER fpp;
