"""Modelos de contenidos prenatales y señales de alerta."""

from sqlalchemy.dialects.mysql import INTEGER as UINT
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.dialects.mysql import SMALLINT
from sqlalchemy.dialects.mysql import TINYINT

from extensions import db


class ContenidoPrenatal(db.Model):
    """Tabla `contenidos_prenatales`: orientación prenatal publicada."""

    __tablename__ = "contenidos_prenatales"

    id = db.Column(UINT(unsigned=True), primary_key=True, autoincrement=True)
    creado_por_usuario_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "usuarios.id",
            name="fk_contenidos_creador",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        nullable=True,
    )
    actualizado_por_usuario_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "usuarios.id",
            name="fk_contenidos_actualizador",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        nullable=True,
    )
    titulo = db.Column(db.String(180), nullable=False)
    resumen = db.Column(db.String(500), nullable=True)
    contenido = db.Column(LONGTEXT, nullable=False)
    categoria = db.Column(db.String(80), nullable=False)
    semana_desde = db.Column(TINYINT(unsigned=True), nullable=True)
    semana_hasta = db.Column(TINYINT(unsigned=True), nullable=True)
    trimestre = db.Column(TINYINT(unsigned=True), nullable=True)
    fuente_nombre = db.Column(db.String(180), nullable=False)
    fuente_url = db.Column(db.String(500), nullable=True)
    fecha_revision = db.Column(db.Date, nullable=False)
    publicado = db.Column(TINYINT(1), nullable=False, server_default=db.text("0"))
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

    creado_por = db.relationship(
        "Usuario",
        back_populates="contenidos_creados",
        foreign_keys=[creado_por_usuario_id],
    )
    actualizado_por = db.relationship(
        "Usuario",
        back_populates="contenidos_actualizados",
        foreign_keys=[actualizado_por_usuario_id],
    )

    __table_args__ = (
        db.Index("idx_contenidos_etapa", "trimestre", "semana_desde", "semana_hasta"),
        db.Index("idx_contenidos_categoria_publicado", "categoria", "publicado"),
        db.CheckConstraint(
            "(semana_desde is null and semana_hasta is null) or "
            "(semana_desde between 1 and 42 and "
            "semana_hasta between semana_desde and 42)",
            name="chk_contenidos_semanas",
        ),
        db.CheckConstraint(
            "trimestre is null or trimestre between 1 and 3",
            name="chk_contenidos_trimestre",
        ),
        db.CheckConstraint("publicado in (0, 1)", name="chk_contenidos_publicado"),
    )

    def __repr__(self) -> str:
        return f"<ContenidoPrenatal id={self.id} publicado={self.publicado}>"


class SenalAlerta(db.Model):
    """Tabla `senales_alerta`: catálogo de señales de alerta."""

    __tablename__ = "senales_alerta"

    id = db.Column(UINT(unsigned=True), primary_key=True, autoincrement=True)
    creado_por_usuario_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "usuarios.id",
            name="fk_senales_creador",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        nullable=True,
    )
    actualizado_por_usuario_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "usuarios.id",
            name="fk_senales_actualizador",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        nullable=True,
    )
    titulo = db.Column(db.String(180), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    accion_recomendada = db.Column(db.Text, nullable=False)
    orden_visual = db.Column(
        SMALLINT(unsigned=True),
        nullable=False,
        server_default=db.text("0"),
    )
    fuente_nombre = db.Column(db.String(180), nullable=False)
    fuente_url = db.Column(db.String(500), nullable=True)
    fecha_revision = db.Column(db.Date, nullable=False)
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

    creada_por = db.relationship(
        "Usuario",
        back_populates="senales_creadas",
        foreign_keys=[creado_por_usuario_id],
    )
    actualizada_por = db.relationship(
        "Usuario",
        back_populates="senales_actualizadas",
        foreign_keys=[actualizado_por_usuario_id],
    )

    __table_args__ = (
        db.Index("idx_senales_activo_orden", "activo", "orden_visual"),
        db.CheckConstraint("activo in (0, 1)", name="chk_senales_activo"),
    )

    def __repr__(self) -> str:
        return f"<SenalAlerta id={self.id} activo={self.activo}>"
