import pyotp  # Para 2FA
from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from app.modules.auth import auth_bp
from app.modules.auth.forms import LoginForm, SignupForm
from app.modules.auth.services import AuthenticationService
from app.modules.profile.services import UserProfileService

authentication_service = AuthenticationService()
user_profile_service = UserProfileService()


@auth_bp.route("/signup/", methods=["GET", "POST"])
def show_signup_form():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        if not authentication_service.is_email_available(email):
            return render_template("auth/signup_form.html", form=form, error=f"Email {email} in use")

        try:
            user = authentication_service.create_with_profile(**form.data)
        except Exception as exc:
            return render_template("auth/signup_form.html", form=form, error=f"Error creating user: {exc}")

        # Log user
        login_user(user, remember=True)
        return redirect(url_for("public.index"))

    return render_template("auth/signup_form.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = authentication_service.repository.get_by_email(email)

        if user is None or not user.check_password(password):
            return render_template("auth/login_form.html", form=form, error="Invalid credentials")

        # Si el usuario tiene 2FA habilitado y confirmado
        if hasattr(user, "profile") and user.profile and user.profile.twofa_enabled and user.profile.twofa_confirmed:
            # Guardamos temporalmente su ID en la sesión para el paso de verificación 2FA
            session["pending_2fa_user_id"] = user.id
            return redirect(url_for("auth.verify_2fa"))
        else:
            # Si no tiene 2FA, login normal
            login_user(user, remember=True)
            return redirect(url_for("public.index"))

    return render_template("auth/login_form.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("public.index"))


@auth_bp.route("/verify-2fa", methods=["GET", "POST"])
def verify_2fa():
    # Verificamos que hay un usuario pendiente de 2FA
    user_id = session.get("pending_2fa_user_id")
    if not user_id:
        flash("There is no session pending 2FA verification.", "error")
        return redirect(url_for("auth.login"))

    user = authentication_service.repository.get_by_id(user_id)
    if not user or not user.profile:
        flash("User not found.", "error")
        return redirect(url_for("public.index"))

    if request.method == "POST":
        token = request.form.get("token")
        secret = user.profile.get_twofa_secret()

        if not secret:
            flash("Authenticator secret code not found.", "error")
            return redirect(url_for("auth.login"))

        totp = pyotp.TOTP(secret)
        if totp.verify(token):
            # Si el código es correcto entonces se completa el login
            login_user(user, remember=True)
            session.pop("pending_2fa_user_id", None)
            return redirect(url_for("public.index"))
        else:
            flash("Invalid code. Try again.", "error")

    return render_template("auth/verify_2fa.html")
