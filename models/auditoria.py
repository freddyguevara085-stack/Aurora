"""Modelo del historial de auditoría administrativa."""

from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.dialects.mysql import INTEGER as UINT
from sqlalchemy.dialects.mysql import JSON

from extensions import db


class HistorialAuditoria(db.Model):
    """Tabla `historial_auditoria`: trazabilidad de acciones administrativas."""

    __tablename__ = "historial_auditoria"

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    usuario_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "usuarios.id",
            name="fk_auditoria_usuario",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        nullable=True,
    )
    accion = db.Column(db.String(50), nullable=False)
    entidad = db.Column(db.String(80), nullable=False)
    registro_id = db.Column(BIGINT(unsigned=True), nullable=True)
    detalles = db.Column(JSON, nullable=True)
    direccion_ip = db.Column(db.String(45), nullable=True)
    created_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=db.text("CURRENT_TIMESTAMP"),
    )

    usuario = db.relationship(
        "Usuario",
        back_populates="registros_auditoria",
        foreign_keys=[usuario_id],
    )

    __table_args__ = (
        db.Index("idx_auditoria_usuario_fecha", "usuario_id", "created_at"),
        db.Index("idx_auditoria_entidad_registro", "entidad", "registro_id"),
        db.Index("idx_auditoria_fecha", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<HistorialAuditoria id={self.id} usuario_id={self.usuario_id}>"
