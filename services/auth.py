"""Servicios de autenticación, tokens de recuperación y envío de correo."""

from email.message import EmailMessage
import hmac
from html import escape
import os
import smtplib
import sys
from urllib.parse import unquote, urlsplit

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from extensions import db
from models.usuario import Usuario


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


def _serializador_recuperacion() -> URLSafeTimedSerializer:
    """Construye el serializador firmado para tokens de recuperación."""
    secret = current_app.config["SECRET_KEY"]
    return URLSafeTimedSerializer(secret, salt=secret)


def generar_token_recuperacion(
    usuario: Usuario,
    serializador: URLSafeTimedSerializer | None = None,
) -> str:
    """Genera un token firmado vinculado a la huella de la contraseña actual."""
    ser = serializador or _serializador_recuperacion()
    payload = {"email": usuario.email, "pwd_stamp": usuario.password_hash[-12:]}
    return ser.dumps(payload)


def verificar_token_recuperacion(
    token: str,
    max_age: int = 3600,
    serializador: URLSafeTimedSerializer | None = None,
) -> Usuario | None:
    """Valida el token de recuperación y devuelve el usuario activo o ``None``."""
    ser = serializador or _serializador_recuperacion()
    try:
        payload = ser.loads(token, max_age=max_age)
        if not isinstance(payload, dict) or not payload.get("email") or not payload.get("pwd_stamp"):
            return None
    except (SignatureExpired, BadSignature):
        return None

    usuario = db.session.scalar(
        db.select(Usuario).filter_by(email=payload["email"], activo=1)
    )
    if not usuario or not hmac.compare_digest(usuario.password_hash[-12:], payload["pwd_stamp"]):
        return None
    return usuario


def _enmascarar_email(email: str) -> str:
    """Oculta la parte local de un correo, dejando el dominio visible para diagnóstico."""
    if "@" not in email:
        return "***"
    local, domain = email.rsplit("@", 1)
    if not local:
        return f"***@{domain}"
    if len(local) == 1:
        return f"{local[0]}***@{domain}"
    return f"{local[0]}***{local[-1]}@{domain}"


def enviar_correo_recuperacion(destinatario: str, enlace: str) -> None:
    """Envía el enlace por SMTP o lo muestra solo en consola durante DEBUG local."""
    servidor = os.getenv("MAIL_SERVER") or current_app.config.get("MAIL_SERVER")
    if not servidor:
        if current_app.config.get("DEBUG"):
            print(f"Enlace de recuperación para {destinatario}: {enlace}", file=sys.stdout)
        else:
            current_app.logger.warning(
                "MAIL_SERVER no configurado. No se envió correo de recuperación a %s",
                destinatario,
            )
        return

    puerto = int(os.getenv("MAIL_PORT") or current_app.config.get("MAIL_PORT", 587))
    usar_tls_env = os.getenv("MAIL_USE_TLS")
    if usar_tls_env is not None:
        usar_tls = usar_tls_env.strip().lower() in {"1", "true", "yes", "on"}
    else:
        usar_tls = bool(current_app.config.get("MAIL_USE_TLS", True))
    usuario_smtp = os.getenv("MAIL_USERNAME") or current_app.config.get("MAIL_USERNAME")
    password_smtp = os.getenv("MAIL_PASSWORD") or current_app.config.get("MAIL_PASSWORD")
    remitente = (
        os.getenv("MAIL_DEFAULT_SENDER")
        or current_app.config.get("MAIL_DEFAULT_SENDER")
        or usuario_smtp
    )
    if not remitente:
        raise RuntimeError(
            "MAIL_DEFAULT_SENDER debe estar definida cuando MAIL_SERVER está configurado."
        )

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
