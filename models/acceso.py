"""
Modelos de control de acceso: Rol, Permiso, RolPermiso.

Tablas representadas : roles, permisos, roles_permisos
Fuente SQL           : Aurora_BD.sql líneas 11-74
SQLAlchemy           : 2.0.x  (usa dialecto MySQL para INT UNSIGNED)
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

    # Acceso a la fila completa de roles_permisos (incluye asignado_at)
    asignaciones_permisos = db.relationship(
        "RolPermiso",
        back_populates="rol",
        cascade="all, delete-orphan",
    )
    # Acceso directo a Permiso a través de la tabla asociativa (solo lectura)
    permisos = db.relationship(
        "Permiso",
        secondary="roles_permisos",
        back_populates="roles",
        viewonly=True,
    )
    usuarios = db.relationship("Usuario", back_populates="rol")

    __table_args__ = (
        db.UniqueConstraint("nombre", name="uk_roles_nombre"),
    )

    def __repr__(self) -> str:
        return f"<Rol id={self.id} nombre={self.nombre!r}>"


class Permiso(db.Model):
    """Tabla `permisos`: catálogo de permisos atómicos del sistema."""

    __tablename__ = "permisos"

    id = db.Column(UINT(unsigned=True), primary_key=True, autoincrement=True)
    codigo = db.Column(db.String(80), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    created_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    # Acceso a la fila completa de roles_permisos
    asignaciones_roles = db.relationship(
        "RolPermiso",
        back_populates="permiso",
        cascade="all, delete-orphan",
    )
    # Acceso directo a Rol a través de la tabla asociativa (solo lectura)
    roles = db.relationship(
        "Rol",
        secondary="roles_permisos",
        back_populates="permisos",
        viewonly=True,
    )

    __table_args__ = (
        db.UniqueConstraint("codigo", name="uk_permisos_codigo"),
        db.UniqueConstraint("nombre", name="uk_permisos_nombre"),
    )

    def __repr__(self) -> str:
        return f"<Permiso id={self.id} codigo={self.codigo!r}>"


class RolPermiso(db.Model):
    """Tabla `roles_permisos`: asociación M-N entre roles y permisos."""

    __tablename__ = "roles_permisos"

    rol_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "roles.id",
            name="fk_roles_permisos_rol",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        primary_key=True,
    )
    permiso_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "permisos.id",
            name="fk_roles_permisos_permiso",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        primary_key=True,
    )
    asignado_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    rol = db.relationship("Rol", back_populates="asignaciones_permisos")
    permiso = db.relationship("Permiso", back_populates="asignaciones_roles")

    __table_args__ = (
        db.Index("idx_roles_permisos_permiso", "permiso_id"),
    )

    def __repr__(self) -> str:
        return f"<RolPermiso rol_id={self.rol_id} permiso_id={self.permiso_id}>"
