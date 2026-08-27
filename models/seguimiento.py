"""Modelos de controles prenatales y recordatorios."""

from sqlalchemy.dialects.mysql import ENUM
from sqlalchemy.dialects.mysql import INTEGER as UINT
from sqlalchemy.dialects.mysql import SMALLINT
from sqlalchemy.dialects.mysql import TINYINT

from extensions import db


class ControlPrenatal(db.Model):
    """Tabla `controles_prenatales`: organización de controles prenatales."""

    __tablename__ = "controles_prenatales"

    id = db.Column(UINT(unsigned=True), primary_key=True, autoincrement=True)
    embarazo_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "embarazos.id",
            name="fk_controles_embarazo",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=False,
    )
    centro_atencion_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "centros_atencion.id",
            name="fk_controles_centro",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        nullable=True,
    )
    registrado_por_usuario_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "usuarios.id",
            name="fk_controles_usuario",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=False,
    )
    numero_control = db.Column(SMALLINT(unsigned=True), nullable=False)
    fecha_control = db.Column(db.Date, nullable=False)
    hora_control = db.Column(db.Time, nullable=True)
    edad_gestacional_semanas = db.Column(db.Numeric(4, 1), nullable=True)
    estado = db.Column(
        ENUM("programado", "realizado", "reprogramado", "cancelado"),
        nullable=False,
        server_default=db.text("'programado'"),
    )
    indicaciones = db.Column(db.Text, nullable=True)
    notas = db.Column(db.Text, nullable=True)
    fecha_siguiente_control = db.Column(db.Date, nullable=True)
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

    embarazo = db.relationship(
        "Embarazo",
        back_populates="controles_prenatales",
        foreign_keys=[embarazo_id],
    )
    centro_atencion = db.relationship(
        "CentroAtencion",
        back_populates="controles_prenatales",
        foreign_keys=[centro_atencion_id],
    )
    registrado_por_usuario = db.relationship(
        "Usuario",
        back_populates="controles_registrados",
        foreign_keys=[registrado_por_usuario_id],
    )
    recordatorios = db.relationship(
        "Recordatorio",
        back_populates="control_prenatal",
        foreign_keys="Recordatorio.control_prenatal_id",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "embarazo_id",
            "numero_control",
            name="uk_controles_embarazo_numero",
        ),
        db.Index("idx_controles_fecha_estado", "fecha_control", "estado"),
        db.Index("idx_controles_centro", "centro_atencion_id"),
        db.Index("idx_controles_usuario", "registrado_por_usuario_id"),
        db.CheckConstraint("numero_control > 0", name="chk_controles_numero"),
        db.CheckConstraint(
            "edad_gestacional_semanas is null "
            "or edad_gestacional_semanas between 0 and 45",
            name="chk_controles_edad_gestacional",
        ),
    )

    def __repr__(self) -> str:
        return f"<ControlPrenatal id={self.id} estado={self.estado!r}>"


class Recordatorio(db.Model):
    """Tabla `recordatorios`: avisos asociados a usuarios y controles."""

    __tablename__ = "recordatorios"

    id = db.Column(UINT(unsigned=True), primary_key=True, autoincrement=True)
    usuario_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "usuarios.id",
            name="fk_recordatorios_usuario",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=False,
    )
    control_prenatal_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "controles_prenatales.id",
            name="fk_recordatorios_control",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        nullable=True,
    )
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.String(500), nullable=True)
    tipo = db.Column(
        ENUM("control", "personal", "informativo"),
        nullable=False,
        server_default=db.text("'personal'"),
    )
    fecha_hora = db.Column(db.DateTime, nullable=False)
    estado = db.Column(
        ENUM("pendiente", "enviado", "completado", "cancelado"),
        nullable=False,
        server_default=db.text("'pendiente'"),
    )
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

    usuario = db.relationship(
        "Usuario",
        back_populates="recordatorios",
        foreign_keys=[usuario_id],
    )
    control_prenatal = db.relationship(
        "ControlPrenatal",
        back_populates="recordatorios",
        foreign_keys=[control_prenatal_id],
    )

    __table_args__ = (
        db.Index("idx_recordatorios_usuario_fecha", "usuario_id", "fecha_hora"),
        db.Index("idx_recordatorios_estado_fecha", "estado", "fecha_hora"),
        db.Index("idx_recordatorios_control", "control_prenatal_id"),
    )

    def __repr__(self) -> str:
        return f"<Recordatorio id={self.id} estado={self.estado!r}>"
