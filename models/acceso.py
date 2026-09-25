"""
Modelo de control de acceso: Rol.

Tabla representada : roles
Fuente SQL         : Aurora_BD.sql líneas 11-74
SQLAlchemy         : 2.0.x  (usa dialecto MySQL para INT UNSIGNED)
"""

from sqlalchemy.dialects.mysql import INTEGER as UINT

from extensions import db


class Rol(db.Model):
    """Tabla `roles`: catálogo de roles del sistema."""

    __tablename__ = "roles"

    id = db.Column(UINT(unsigned=True), primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    created_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    usuarios = db.relationship("Usuario", back_populates="rol")

    __table_args__ = (
        db.UniqueConstraint("nombre", name="uk_roles_nombre"),
    )

    def __repr__(self) -> str:
        return f"<Rol id={self.id} nombre={self.nombre!r}>"
