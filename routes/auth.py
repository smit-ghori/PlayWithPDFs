"""Authentication blueprint for end-users (PlayWithPDFs).
Provides registration, login, logout, and profile management.
"""

from functools import wraps
import re
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app)
from extensions import db
from models import User, utcnow, DEPARTMENTS

auth_bp = Blueprint("auth", __name__)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_current_user():
    """Retrieve the logged-in User instance from the current session."""
    uid = session.get("user_id")
    if uid:
        try:
            return User.query.get(uid)
        except Exception:
            return None
    return None


def is_safe_url(target):
    """Check that the redirect URL is relative and not an open redirect or auth loop."""
    if not target or not isinstance(target, str):
        return False
    target = target.strip()
    if target.startswith("/") and not target.startswith("//") and not target.startswith("/login") and not target.startswith("/register"):
        return True
    return False


def user_login_required(view):
    """Decorator to protect routes that require end-user authentication."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_active:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapper


@auth_bp.app_context_processor
def inject_current_user():
    """Make current_user available in all templates globally."""
    return {"current_user": get_current_user()}


# =============================================================================
# REGISTER
# =============================================================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if get_current_user():
        return redirect(url_for("home.home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").lower().strip()
        department = request.form.get("department", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if department not in DEPARTMENTS:
            department = "General / Other"

        # Validation
        if not name or len(name) < 2:
            flash("Please enter a valid full name (at least 2 characters).", "error")
            return render_template("auth/register.html", name=name, email=email, selected_department=department, departments=DEPARTMENTS)

        if not email or not EMAIL_REGEX.match(email):
            flash("Please enter a valid email address.", "error")
            return render_template("auth/register.html", name=name, email=email, selected_department=department, departments=DEPARTMENTS)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("auth/register.html", name=name, email=email, selected_department=department, departments=DEPARTMENTS)

        if password != confirm_password:
            flash("Passwords do not match. Please verify and try again.", "error")
            return render_template("auth/register.html", name=name, email=email, selected_department=department, departments=DEPARTMENTS)

        # Check existing account
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("An account with this email address already exists. Please log in instead.", "error")
            return redirect(url_for("auth.login", email=email))

        try:
            new_user = User(name=name, email=email, department=department, is_active=True)
            new_user.set_password(password)
            new_user.last_login_at = utcnow()
            db.session.add(new_user)
            db.session.commit()

            # Auto-login upon registration
            session.permanent = True
            session["user_id"] = new_user.id

            flash(f"Welcome to PlayWithPDFs, {new_user.name}! Your account has been created under {department}.", "success")
            next_url = request.args.get("next") or request.form.get("next")
            if is_safe_url(next_url):
                return redirect(next_url)
            return redirect(url_for("home.home"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error registering user {email}: {e}")
            flash("An error occurred during registration. Please try again.", "error")
            return render_template("auth/register.html", name=name, email=email, selected_department=department, departments=DEPARTMENTS)

    return render_template("auth/register.html", departments=DEPARTMENTS)


# =============================================================================
# LOGIN
# =============================================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if get_current_user():
        return redirect(url_for("home.home"))

    email_prefill = request.args.get("email", "").strip()

    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template("auth/login.html", email=email)

        user = User.query.filter_by(email=email).first()

        if user and user.is_active and user.check_password(password):
            session.permanent = remember
            session["user_id"] = user.id
            user.last_login_at = utcnow()
            db.session.commit()

            flash(f"Welcome back, {user.name}!", "success")
            next_url = request.args.get("next") or request.form.get("next")
            if is_safe_url(next_url):
                return redirect(next_url)
            return redirect(url_for("home.home"))

        flash("Invalid email or password. Please check your credentials.", "error")
        return render_template("auth/login.html", email=email), 401

    return render_template("auth/login.html", email=email_prefill)


# =============================================================================
# LOGOUT
# =============================================================================

@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("home.home"))


# =============================================================================
# PROFILE / ACCOUNT
# =============================================================================

@auth_bp.route("/profile", methods=["GET", "POST"])
@user_login_required
def profile():
    user = get_current_user()

    if request.method == "POST":
        new_name = request.form.get("name", "").strip()
        new_dept = request.form.get("department", "").strip()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not new_name or len(new_name) < 2:
            flash("Full name must be at least 2 characters.", "error")
            return render_template("auth/profile.html", user=user, departments=DEPARTMENTS)

        user.name = new_name
        if new_dept in DEPARTMENTS:
            user.department = new_dept

        # Password update requested
        if current_password or new_password or confirm_password:
            if not user.check_password(current_password):
                flash("Your current password is incorrect.", "error")
                return render_template("auth/profile.html", user=user, departments=DEPARTMENTS)

            if len(new_password) < 6:
                flash("New password must be at least 6 characters long.", "error")
                return render_template("auth/profile.html", user=user, departments=DEPARTMENTS)

            if new_password != confirm_password:
                flash("New passwords do not match.", "error")
                return render_template("auth/profile.html", user=user, departments=DEPARTMENTS)

            user.set_password(new_password)
            flash("Password and profile updated successfully!", "success")
        else:
            flash("Profile updated successfully!", "success")

        try:
            db.session.commit()
            return redirect(url_for("auth.profile"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating profile: {e}")
            flash("An error occurred while saving your changes.", "error")

    return render_template("auth/profile.html", user=user, departments=DEPARTMENTS)
