"""Rutas de autenticación de Aurora."""

import hmac
import os
import smtplib
import sys
from email.message import EmailMessage
from html import escape
from urllib.parse import unquote, urlsplit

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, login_required, logout_user
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.security import generate_password_hash

from extensions import db, login_manager
from models.acceso import Rol
from models.gestacion import PerfilGestante
from models.usuario import Usuario


auth_bp = Blueprint("auth", __name__)


def normalizar_next_local(next_url: str | None) -> str | None:
    """Normaliza hasta tres veces y permite únicamente rutas locales seguras."""
    if not next_url:
        return None

    normalized = next_url
    for _ in range(3):
        decoded = unquote(normalized)
        if decoded == normalized:
            break
        normalized = decoded
    else:
        if unquote(normalized) != normalized:
            return None

    if (
        any(ord(char) <= 31 or ord(char) == 127 for char in normalized)
        or "\\" in normalized
        or not normalized.startswith("/")
        or normalized.startswith("//")
    ):
        return None

    parsed = urlsplit(normalized)
    if parsed.scheme or parsed.netloc:
        return None

    return normalized


@login_manager.user_loader
def cargar_usuario(user_id: str) -> Usuario | None:
    try:
        return db.session.get(Usuario, int(user_id))
    except (TypeError, ValueError):
        return None


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.rol and current_user.rol.nombre == "administrador":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        usuario = db.session.scalar(db.select(Usuario).filter_by(email=email))

        if not usuario or not usuario.is_active or not usuario.verificar_password(password):
            flash("Correo o contraseña incorrectos.", "error")
            return render_template("login.html"), 200

        try:
            usuario.ultimo_acceso_at = db.func.now()
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Correo o contraseña incorrectos.", "error")
            return render_template("login.html"), 200

        login_user(usuario, remember=False)
        next_url = normalizar_next_local(request.args.get("next"))
        if not next_url and usuario.rol and usuario.rol.nombre == "administrador":
            return redirect(url_for("admin.dashboard"))
        return redirect(next_url or url_for("main.index"))

    return render_template("login.html")


def _serializador_recuperacion() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"],
        salt=current_app.config["SECRET_KEY"],
    )


def enviar_correo_recuperacion(destinatario: str, enlace: str) -> None:
    """Envía el enlace por SMTP o lo muestra solo en consola durante DEBUG local."""
    servidor = os.getenv("MAIL_SERVER")
    if not servidor:
        if current_app.config.get("DEBUG"):
            print(f"Enlace de recuperación para {destinatario}: {enlace}", file=sys.stdout)
        return

    puerto = int(os.getenv("MAIL_PORT", "587"))
    usar_tls = os.getenv("MAIL_USE_TLS", "1").strip().lower() in {"1", "true", "yes", "on"}
    usuario_smtp = os.getenv("MAIL_USERNAME")
    password_smtp = os.getenv("MAIL_PASSWORD")
    remitente = os.getenv("MAIL_DEFAULT_SENDER") or usuario_smtp
    if not remitente:
        raise RuntimeError("MAIL_DEFAULT_SENDER debe estar definida cuando MAIL_SERVER está configurado.")

    mensaje = EmailMessage()
    mensaje["Subject"] = "Restablece tu contraseña de Aurora"
    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje.set_content(
        "Recibimos una solicitud para restablecer tu contraseña de Aurora. "
        f"Abre este enlace dentro de una hora: {enlace}"
    )
    enlace_html = escape(enlace, quote=True)
    mensaje.add_alternative(
        "<p>Recibimos una solicitud para restablecer tu contraseña de Aurora.</p>"
        f'<p><a href="{enlace_html}">Restablecer contraseña</a></p>'
        "<p>Este enlace vence en una hora y solo puede utilizarse una vez.</p>",
        subtype="html",
    )

    with smtplib.SMTP(servidor, puerto, timeout=10) as smtp:
        if usar_tls:
            smtp.starttls()
        if usuario_smtp:
            smtp.login(usuario_smtp, password_smtp or "")
        smtp.send_message(mensaje)


@auth_bp.route("/recuperar-password", methods=["GET", "POST"])
def recuperar_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()[:150]
        if email:
            usuario = db.session.scalar(db.select(Usuario).filter_by(email=email, activo=1))
            if usuario:
                payload = {"email": usuario.email, "pwd_stamp": usuario.password_hash[-12:]}
                token = _serializador_recuperacion().dumps(payload)
                enlace = url_for("auth.restablecer_password", token=token, _external=True)
                current_app.logger.info("Solicitud de recuperación para correo: %s", usuario.email)
                try:
                    enviar_correo_recuperacion(usuario.email, enlace)
                except (OSError, RuntimeError, smtplib.SMTPException):
                    current_app.logger.exception("No fue posible enviar la recuperación para correo: %s", usuario.email)
        flash("Si el correo está registrado, se enviaron las instrucciones para restablecer tu contraseña.", "success")
        return redirect(url_for("auth.login"))

    return render_template("recuperar_password.html")


@auth_bp.route("/restablecer-password/<token>", methods=["GET", "POST"])
def restablecer_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    try:
        payload = _serializador_recuperacion().loads(token, max_age=3600)
        if not isinstance(payload, dict) or not payload.get("email") or not payload.get("pwd_stamp"):
            raise BadSignature
    except (SignatureExpired, BadSignature):
        flash("El enlace de recuperación no es válido o ha expirado.", "error")
        return redirect(url_for("auth.recuperar_password"))

    email = payload["email"]
    usuario = db.session.scalar(db.select(Usuario).filter_by(email=email, activo=1))
    if not usuario or not hmac.compare_digest(usuario.password_hash[-12:], payload["pwd_stamp"]):
        flash("El enlace de recuperación no es válido o ha expirado.", "error")
        return redirect(url_for("auth.recuperar_password"))

    if request.method == "POST":
        nueva = request.form.get("password", "")
        confirmacion = request.form.get("password_confirm", "")
        if len(nueva) < 8 or nueva != confirmacion:
            flash("Confirma una contraseña de al menos 8 caracteres.", "error")
            return render_template("restablecer_password.html", token=token)
        usuario.password_hash = generate_password_hash(nueva)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("No fue posible actualizar la contraseña.", "error")
            return render_template("restablecer_password.html", token=token)
        flash("Contraseña restablecida. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("restablecer_password.html", token=token)


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        nombres = request.form.get("nombres", "").strip()[:100]
        email = request.form.get("email", "").strip().lower()[:150]
        password = request.form.get("password", "")
        confirmacion = request.form.get("password_confirm", "")
        rol = db.session.scalar(db.select(Rol).filter_by(nombre="usuario"))

        if not nombres or not email or len(password) < 8 or password != confirmacion:
            flash("Completa los datos y confirma una contraseña de al menos 8 caracteres.", "error")
            return render_template("registro.html"), 400
        if not rol or db.session.scalar(db.select(Usuario).filter_by(email=email)):
            flash("No fue posible crear la cuenta con esos datos.", "error")
            return render_template("registro.html"), 400

        try:
            usuario = Usuario(
                rol_id=rol.id,
                nombres=nombres,
                apellidos="",
                email=email,
                password_hash=generate_password_hash(password),
                activo=1,
            )
            db.session.add(usuario)
            db.session.flush()
            db.session.add(PerfilGestante(usuario_id=usuario.id))
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("No fue posible crear la cuenta con esos datos.", "error")
            return render_template("registro.html"), 400

        flash("Cuenta creada. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("registro.html")


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
