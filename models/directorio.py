"""Modelos del directorio de centros de atención y servicios."""

from sqlalchemy.dialects.mysql import ENUM
from sqlalchemy.dialects.mysql import INTEGER as UINT
from sqlalchemy.dialects.mysql import TINYINT

from extensions import db


class CentroAtencion(db.Model):
    """Tabla `centros_atencion`: directorio de establecimientos de salud."""

    __tablename__ = "centros_atencion"

    id = db.Column(UINT(unsigned=True), primary_key=True, autoincrement=True)
    codigo_minsa = db.Column(db.String(20), nullable=True)
    nombre = db.Column(db.String(150), nullable=False)
    tipo_establecimiento = db.Column(
        ENUM(
            "hospital",
            "centro_salud",
            "puesto_salud",
            "casa_materna",
            "clinica",
            "otro",
        ),
        nullable=False,
        server_default=db.text("'centro_salud'"),
    )
    silais = db.Column(db.String(100), nullable=True)
    municipio = db.Column(db.String(100), nullable=False)
    departamento = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.Text, nullable=True)
    telefono = db.Column(db.String(30), nullable=True)
    horario = db.Column(db.String(255), nullable=True)
    latitud = db.Column(db.Numeric(10, 7), nullable=True)
    longitud = db.Column(db.Numeric(10, 7), nullable=True)
    fecha_verificacion = db.Column(db.Date, nullable=True)
    activo = db.Column(TINYINT(1), nullable=False, server_default=db.text("1"))
    created_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )
    updated_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )

    asignaciones_servicios = db.relationship(
        "CentroServicio",
        back_populates="centro_atencion",
        cascade="all, delete-orphan",
    )
    controles_prenatales = db.relationship(
        "ControlPrenatal",
        back_populates="centro_atencion",
        foreign_keys="ControlPrenatal.centro_atencion_id",
    )

    __table_args__ = (
        db.UniqueConstraint("codigo_minsa", name="uk_centros_codigo_minsa"),
        db.Index("idx_centros_nombre", "nombre"),
        db.Index("idx_centros_ubicacion", "departamento", "municipio"),
        db.Index("idx_centros_tipo", "tipo_establecimiento"),
        db.CheckConstraint("activo in (0, 1)", name="chk_centros_activo"),
        db.CheckConstraint(
            "latitud is null or latitud between -90 and 90",
            name="chk_centros_latitud",
        ),
        db.CheckConstraint(
            "longitud is null or longitud between -180 and 180",
            name="chk_centros_longitud",
        ),
    )

    def __repr__(self) -> str:
        return f"<CentroAtencion id={self.id}>"


class Servicio(db.Model):
    """Tabla `servicios`: catálogo de servicios de atención."""

    __tablename__ = "servicios"

    id = db.Column(UINT(unsigned=True), primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.String(500), nullable=True)
    activo = db.Column(TINYINT(1), nullable=False, server_default=db.text("1"))
    created_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )
    updated_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )

    asignaciones_centros = db.relationship(
        "CentroServicio",
        back_populates="servicio",
    )

    __table_args__ = (
        db.UniqueConstraint("nombre", name="uk_servicios_nombre"),
        db.Index("idx_servicios_activo", "activo"),
        db.CheckConstraint("activo in (0, 1)", name="chk_servicios_activo"),
    )

    def __repr__(self) -> str:
        return f"<Servicio id={self.id}>"


class CentroServicio(db.Model):
    """Tabla `centros_servicios`: disponibilidad de servicios por centro."""

    __tablename__ = "centros_servicios"

    centro_atencion_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "centros_atencion.id",
            name="fk_centros_servicios_centro",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        primary_key=True,
    )
    servicio_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "servicios.id",
            name="fk_centros_servicios_servicio",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        primary_key=True,
    )
    disponible = db.Column(TINYINT(1), nullable=False, server_default=db.text("1"))
    observaciones = db.Column(db.String(255), nullable=True)
    fecha_verificacion = db.Column(db.Date, nullable=True)
    created_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )
    updated_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    )

    centro_atencion = db.relationship(
        "CentroAtencion",
        back_populates="asignaciones_servicios",
    )
    servicio = db.relationship("Servicio", back_populates="asignaciones_centros")

    __table_args__ = (
        db.Index("idx_centros_servicios_servicio", "servicio_id"),
        db.Index("idx_centros_servicios_disponible", "disponible"),
        db.CheckConstraint(
            "disponible in (0, 1)",
            name="chk_centros_servicios_disponible",
        ),
    )

    def __repr__(self) -> str:
        return (
            "<CentroServicio "
            f"centro_atencion_id={self.centro_atencion_id} servicio_id={self.servicio_id}>"
        )
