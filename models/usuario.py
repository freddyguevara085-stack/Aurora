"""Modelo de usuarios de Aurora."""

from sqlalchemy.dialects.mysql import INTEGER as UINT
from sqlalchemy.dialects.mysql import TINYINT

from extensions import db


class Usuario(db.Model):
    """Tabla `usuarios`: cuentas de acceso al sistema."""

    __tablename__ = "usuarios"

    id = db.Column(UINT(unsigned=True), primary_key=True, autoincrement=True)
    rol_id = db.Column(
        UINT(unsigned=True),
        db.ForeignKey(
            "roles.id",
            name="fk_usuarios_roles",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=False,
    )
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    activo = db.Column(TINYINT(1), nullable=False, server_default=db.text("1"))
    ultimo_acceso_at = db.Column(db.DateTime, nullable=True)
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

    rol = db.relationship("Rol", back_populates="usuarios")
    perfil_gestante = db.relationship(
        "PerfilGestante",
        back_populates="usuario",
        uselist=False,
    )
    controles_registrados = db.relationship(
        "ControlPrenatal",
        back_populates="registrado_por_usuario",
        foreign_keys="ControlPrenatal.registrado_por_usuario_id",
    )
    recordatorios = db.relationship(
        "Recordatorio",
        back_populates="usuario",
        foreign_keys="Recordatorio.usuario_id",
    )
    contenidos_creados = db.relationship(
        "ContenidoPrenatal",
        back_populates="creado_por",
        foreign_keys="ContenidoPrenatal.creado_por_usuario_id",
    )
    contenidos_actualizados = db.relationship(
        "ContenidoPrenatal",
        back_populates="actualizado_por",
        foreign_keys="ContenidoPrenatal.actualizado_por_usuario_id",
    )
    senales_creadas = db.relationship(
        "SenalAlerta",
        back_populates="creada_por",
        foreign_keys="SenalAlerta.creado_por_usuario_id",
    )
    senales_actualizadas = db.relationship(
        "SenalAlerta",
        back_populates="actualizada_por",
        foreign_keys="SenalAlerta.actualizado_por_usuario_id",
    )
    registros_auditoria = db.relationship(
        "HistorialAuditoria",
        back_populates="usuario",
        foreign_keys="HistorialAuditoria.usuario_id",
    )

    __table_args__ = (
        db.UniqueConstraint("email", name="uk_usuarios_email"),
        db.Index("idx_usuarios_rol_activo", "rol_id", "activo"),
        db.CheckConstraint("activo in (0, 1)", name="chk_usuarios_activo"),
    )

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} rol_id={self.rol_id}>"
