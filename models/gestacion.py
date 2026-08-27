"""Modelos de perfil gestante y seguimiento del embarazo."""

from sqlalchemy.dialects.mysql import ENUM
from sqlalchemy.dialects.mysql import INTEGER as UINT
from sqlalchemy.dialects.mysql import TINYINT

from extensions import db


class PerfilGestante(db.Model):
    """Tabla `perfiles_gestantes`: perfil no clínico de la usuaria."""

    __tablename__ = "perfiles_gestantes"

    id = db.Column(UINT(unsigned=True), primary_key=True, autoincrement=True)
    usuario_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "usuarios.id",
            name="fk_perfiles_usuario",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=False,
    )
    cedula = db.Column(db.String(20), nullable=True)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    telefono = db.Column(db.String(30), nullable=True)
    direccion_residencia = db.Column(db.Text, nullable=True)
    municipio = db.Column(db.String(100), nullable=True)
    departamento = db.Column(db.String(100), nullable=True)
    contacto_emergencia_nombre = db.Column(db.String(150), nullable=True)
    contacto_emergencia_telefono = db.Column(db.String(30), nullable=True)
    consentimiento_datos = db.Column(
        TINYINT(1),
        nullable=False,
        server_default=db.text("0"),
    )
    fecha_consentimiento = db.Column(db.DateTime, nullable=True)
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

    usuario = db.relationship("Usuario", back_populates="perfil_gestante")
    embarazos = db.relationship("Embarazo", back_populates="perfil_gestante")

    __table_args__ = (
        db.UniqueConstraint("usuario_id", name="uk_perfiles_usuario"),
        db.UniqueConstraint("cedula", name="uk_perfiles_cedula"),
        db.CheckConstraint(
            "consentimiento_datos in (0, 1)",
            name="chk_perfiles_consentimiento",
        ),
        db.CheckConstraint(
            "consentimiento_datos = 0 or fecha_consentimiento is not null",
            name="chk_perfiles_fecha_consentimiento",
        ),
    )

    def __repr__(self) -> str:
        return f"<PerfilGestante id={self.id} usuario_id={self.usuario_id}>"


class Embarazo(db.Model):
    """Tabla `embarazos`: seguimiento de un embarazo de la gestante."""

    __tablename__ = "embarazos"

    id = db.Column(UINT(unsigned=True), primary_key=True, autoincrement=True)
    perfil_gestante_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "perfiles_gestantes.id",
            name="fk_embarazos_perfil",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=False,
    )
    fum = db.Column(db.Date, nullable=True)
    fpp = db.Column(db.Date, nullable=True)
    metodo_fpp = db.Column(
        ENUM("fum", "ecografia", "profesional", "otro"),
        nullable=True,
    )
    estado = db.Column(
        ENUM("activo", "finalizado", "archivado"),
        nullable=False,
        server_default=db.text("'activo'"),
    )
    fecha_fin = db.Column(db.Date, nullable=True)
    notas_personales = db.Column(db.Text, nullable=True)
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

    perfil_gestante = db.relationship("PerfilGestante", back_populates="embarazos")

    __table_args__ = (
        db.Index("idx_embarazos_perfil_estado", "perfil_gestante_id", "estado"),
        db.CheckConstraint(
            "fum is not null or fpp is not null",
            name="chk_embarazos_fechas",
        ),
    )

    def __repr__(self) -> str:
        return f"<Embarazo id={self.id} perfil_gestante_id={self.perfil_gestante_id}>"
