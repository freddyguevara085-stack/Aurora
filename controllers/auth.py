"""Rutas de autenticación de Aurora."""

from urllib.parse import unquote, urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, login_required, logout_user
from sqlalchemy.exc import IntegrityError
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
