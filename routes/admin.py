"""Admin panel blueprint. Mount at /admin."""

import os
import csv
import io
import shutil
import time
import threading
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, Response, abort, current_app)
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask_mail import Message
from sqlalchemy import func, desc

from extensions import db, mail
from models import AdminUser, ToolConfig, ToolEvent, ContactMessage, AuditLog, record_audit, utcnow
from utils.tracking import invalidate_flags, seed_tools

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")


# ---------------------------------------------------------------- auth

def current_admin():
    uid = session.get("admin_id")
    return AdminUser.query.get(uid) if uid else None


def login_required(view):
    @wraps(view)
    def wrapper(*a, **kw):
        user = current_admin()
        if not user or not user.is_active:
            return redirect(url_for("admin.login", next=request.path))
        return view(*a, **kw)
    return wrapper


def editor_required(view):
    @wraps(view)
    @login_required
    def wrapper(*a, **kw):
        if current_admin().role != "admin":
            abort(403)
        return view(*a, **kw)
    return wrapper


@admin_bp.app_context_processor
def _inject():
    return {"admin_user": current_admin()}


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = AdminUser.query.filter_by(email=request.form.get("email", "").lower().strip()).first()
        if user and user.is_active and user.check_password(request.form.get("password", "")):
            session.permanent = True
            session["admin_id"] = user.id
            user.last_login_at = utcnow()
            db.session.commit()
            return redirect(request.args.get("next") or url_for("admin.dashboard"))
        return render_template("admin/login.html", error="That email and password don't match."), 401
    return render_template("admin/login.html")


@admin_bp.route("/logout")
def logout():
    session.pop("admin_id", None)
    return redirect(url_for("admin.login"))


import hashlib

# ---------------------------------------------------------------- password reset

def get_reset_serializer():
    secret = current_app.config.get("SECRET_KEY", "fallback-secret")
    return URLSafeTimedSerializer(secret, salt="admin-password-reset")


def _pwhash_fingerprint(user):
    return hashlib.sha256((user.password_hash or "").encode("utf-8")).hexdigest()[:16]


def generate_reset_token(user):
    s = get_reset_serializer()
    return s.dumps({"id": user.id, "pwhash": _pwhash_fingerprint(user)})


def verify_reset_token(token, max_age=3600):
    s = get_reset_serializer()
    try:
        data = s.loads(token, max_age=max_age)
        user = AdminUser.query.get(data.get("id"))
        if not user or not user.is_active:
            return None
        if _pwhash_fingerprint(user) != data.get("pwhash"):
            return None
        return user
    except (BadSignature, SignatureExpired, Exception):
        return None


def _send_reset_email_async(app, msg, user_email, reset_url):
    with app.app_context():
        try:
            mail.send(msg)
            print(f"Password reset email delivered to {user_email}")
        except Exception as e:
            print(f"Failed to send reset email to {user_email}: {e}")
            print(f"[PASSWORD RESET FALLBACK] Reset link:\n{reset_url}\n")
            app.logger.error(f"Failed to send reset email: {e}")


def send_reset_email(user, reset_url):
    mail_username = os.environ.get("MAIL_USERNAME")
    if not mail_username:
        print(f"\n[DEV MODE - PASSWORD RESET] Reset link for {user.email}:\n{reset_url}\n")
        current_app.logger.info(f"Password reset link for {user.email}: {reset_url}")
        return False

    try:
        msg = Message(
            subject="[PlayWithPDFs Admin] Password Reset Request",
            sender=mail_username,
            recipients=[user.email],
        )
        msg.body = f"""Hello {user.name or 'Admin'},

We received a request to reset your password for the PlayWithPDFs admin operations panel.

To set a new password, click the link below (valid for 1 hour):
{reset_url}

If you did not make this request, you can safely ignore this email. Your password will not change.

Best regards,
PlayWithPDFs Team
"""
        thread = threading.Thread(
            target=_send_reset_email_async,
            args=(current_app._get_current_object(), msg, user.email, reset_url),
        )
        thread.daemon = True
        thread.start()
        return True
    except Exception as e:
        print(f"Failed to dispatch reset email to {user.email}: {e}")
        print(f"[PASSWORD RESET FALLBACK] Link:\n{reset_url}\n")
        current_app.logger.error(f"Failed to dispatch reset email: {e}")
        return False


@admin_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        user = AdminUser.query.filter_by(email=email).first()
        dev_link = None
        if user and user.is_active:
            token = generate_reset_token(user)
            reset_url = url_for("admin.reset_password", token=token, _external=True)
            sent = send_reset_email(user, reset_url)
            record_audit(user, "password.forgot_requested", detail=user.email)
            if not sent:
                dev_link = reset_url

        return render_template(
            "admin/forgot_password.html",
            submitted=True,
            dev_link=dev_link,
            message="If an active account exists with that email address, password reset instructions have been sent."
        )

    return render_template("admin/forgot_password.html")


@admin_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = verify_reset_token(token)
    if not user:
        return render_template(
            "admin/reset_password.html",
            invalid=True,
            error="This password reset link is invalid or has expired. Please request a new one."
        ), 400

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if len(password) < 6:
            return render_template(
                "admin/reset_password.html",
                invalid=False,
                error="Password must be at least 6 characters long."
            ), 400

        if password != confirm:
            return render_template(
                "admin/reset_password.html",
                invalid=False,
                error="Passwords do not match. Please try again."
            ), 400

        user.set_password(password)
        db.session.commit()
        record_audit(user, "password.reset_completed", detail=user.email)
        flash("Your password has been reset successfully! Please sign in with your new password.")
        return redirect(url_for("admin.login"))

    return render_template("admin/reset_password.html", invalid=False)


# ---------------------------------------------------------------- dashboard

def _since(days):
    return datetime.now(timezone.utc) - timedelta(days=days)


@admin_bp.route("/")
@login_required
def dashboard():
    day, week = _since(1), _since(7)

    totals = db.session.query(
        func.count(ToolEvent.id),
        func.count(ToolEvent.id).filter(ToolEvent.ok.is_(False)),
        func.coalesce(func.avg(ToolEvent.duration_ms), 0),
        func.coalesce(func.sum(ToolEvent.input_bytes), 0),
        func.count(func.distinct(ToolEvent.visitor)),
    ).filter(ToolEvent.created_at >= day).one()

    top = (db.session.query(ToolEvent.tool, func.count(ToolEvent.id).label("n"),
                            func.count(ToolEvent.id).filter(ToolEvent.ok.is_(False)).label("bad"),
                            func.coalesce(func.avg(ToolEvent.duration_ms), 0).label("ms"))
           .filter(ToolEvent.created_at >= week)
           .group_by(ToolEvent.tool).order_by(desc("n")).limit(12).all())

    date_col = func.date(ToolEvent.created_at) if db.engine.dialect.name == "sqlite" else func.date_trunc("day", ToolEvent.created_at)
    daily = (db.session.query(date_col.label("d"),
                              func.count(ToolEvent.id))
             .filter(ToolEvent.created_at >= _since(14))
             .group_by("d").order_by("d").all())

    slow = (ToolEvent.query.filter(ToolEvent.created_at >= week)
            .order_by(desc(ToolEvent.duration_ms)).limit(8).all())

    return render_template(
        "admin/dashboard.html",
        runs=totals[0], failures=totals[1], avg_ms=int(totals[2]),
        in_bytes=totals[3], visitors=totals[4],
        top=top, daily=daily, slow=slow,
        new_messages=ContactMessage.query.filter_by(status="new").count(),
        storage=_storage_stats(),
    )


# ---------------------------------------------------------------- tools

@admin_bp.route("/tools")
@login_required
def tools():
    q = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip().lower()

    query = ToolConfig.query
    if q:
        query = query.filter(
            (ToolConfig.tool.ilike(f"%{q}%")) |
            (ToolConfig.label.ilike(f"%{q}%")) |
            (ToolConfig.maintenance_note.ilike(f"%{q}%"))
        )
    if status_filter == "live":
        query = query.filter(ToolConfig.enabled.is_(True))
    elif status_filter == "paused":
        query = query.filter(ToolConfig.enabled.is_(False))

    rows = query.order_by(ToolConfig.tool).all()
    all_tools = ToolConfig.query.all()
    total_count = len(all_tools)
    live_count = sum(1 for t in all_tools if t.enabled)
    paused_count = total_count - live_count

    usage = dict(db.session.query(ToolEvent.tool, func.count(ToolEvent.id))
                 .filter(ToolEvent.created_at >= _since(30))
                 .group_by(ToolEvent.tool).all())
    return render_template(
        "admin/tools.html",
        rows=rows,
        usage=usage,
        q=q,
        status_filter=status_filter,
        total_count=total_count,
        live_count=live_count,
        paused_count=paused_count
    )


@admin_bp.route("/tools/sync", methods=["POST"])
@editor_required
def tools_sync():
    from flask import current_app
    n = seed_tools(current_app)
    invalidate_flags()
    record_audit(current_admin(), "tools.sync", detail=f"{n} added")
    flash(f"Added {n} tools.")
    return redirect(url_for("admin.tools"))


@admin_bp.route("/tools/<tool>", methods=["POST"])
@editor_required
def tool_update(tool):
    cfg = ToolConfig.query.filter_by(tool=tool).first_or_404()
    cfg.enabled = request.form.get("enabled") == "on"
    cfg.label = request.form.get("label") or cfg.label
    cfg.maintenance_note = request.form.get("note") or None
    cfg.max_file_mb = int(request.form.get("max_file_mb") or 50)
    cfg.max_files = int(request.form.get("max_files") or 20)
    db.session.commit()
    invalidate_flags()
    record_audit(current_admin(), "tool.update", tool,
                 f"enabled={cfg.enabled} max_files={cfg.max_files}")
    flash(f"Saved {cfg.label}.")
    q = request.args.get("q") or request.form.get("_q") or ""
    status_filter = request.args.get("status") or request.form.get("_status") or ""
    return redirect(url_for("admin.tools", q=q if q else None, status=status_filter if status_filter else None))


# ---------------------------------------------------------------- events

@admin_bp.route("/events")
@login_required
def events():
    q = ToolEvent.query
    tool = request.args.get("tool")
    if tool:
        q = q.filter(ToolEvent.tool == tool)
    if request.args.get("only") == "failed":
        q = q.filter(ToolEvent.ok.is_(False))
    page = int(request.args.get("page", 1))
    rows = q.order_by(desc(ToolEvent.created_at)).paginate(page=page, per_page=50, error_out=False)
    tools_list = [r.tool for r in ToolConfig.query.order_by(ToolConfig.tool).all()]
    return render_template("admin/events.html", rows=rows, tools=tools_list,
                           tool=tool, only=request.args.get("only", ""))


@admin_bp.route("/events.csv")
@login_required
def events_csv():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["time", "tool", "status", "ms", "in_bytes", "out_bytes", "files", "error"])
    for e in ToolEvent.query.filter(ToolEvent.created_at >= _since(30)).order_by(ToolEvent.created_at):
        w.writerow([e.created_at, e.tool, e.status_code, e.duration_ms,
                    e.input_bytes, e.output_bytes, e.file_count, (e.error_text or "")[:200]])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=tool_events.csv"})


# ---------------------------------------------------------------- messages

@admin_bp.route("/messages")
@login_required
def messages():
    status = request.args.get("status", "new")
    q = ContactMessage.query
    if status != "all":
        q = q.filter_by(status=status)
    return render_template("admin/messages.html", status=status,
                           rows=q.order_by(desc(ContactMessage.created_at)).limit(200).all())


@admin_bp.route("/messages/<int:mid>/<action>", methods=["POST"])
@editor_required
def message_action(mid, action):
    m = ContactMessage.query.get_or_404(mid)
    if action in ("open", "closed", "new"):
        m.status = action
        m.handled_at = utcnow()
        db.session.commit()
        record_audit(current_admin(), "message." + action, str(mid))
    return redirect(request.referrer or url_for("admin.messages"))


# ---------------------------------------------------------------- storage

def _storage_stats():
    total, folders, oldest = 0, 0, None
    if os.path.isdir(UPLOAD_FOLDER):
        for name in os.listdir(UPLOAD_FOLDER):
            p = os.path.join(UPLOAD_FOLDER, name)
            if os.path.isdir(p):
                folders += 1
                age = time.time() - os.path.getmtime(p)
                oldest = age if oldest is None else max(oldest, age)
                for root, _, files in os.walk(p):
                    total += sum(os.path.getsize(os.path.join(root, f)) for f in files)
    return {"bytes": total, "folders": folders, "oldest_min": int((oldest or 0) / 60)}


@admin_bp.route("/storage/purge", methods=["POST"])
@editor_required
def storage_purge():
    freed = _storage_stats()["bytes"]
    for name in os.listdir(UPLOAD_FOLDER):
        p = os.path.join(UPLOAD_FOLDER, name)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
    record_audit(current_admin(), "storage.purge", detail=str(freed))
    flash("Working folder cleared.")
    return redirect(url_for("admin.dashboard"))


# ---------------------------------------------------------------- team

@admin_bp.route("/team", methods=["GET", "POST"])
@editor_required
def team():
    if request.method == "POST":
        email = request.form["email"].lower().strip()
        if AdminUser.query.filter_by(email=email).first():
            flash("That email already has an account.")
        else:
            u = AdminUser(email=email, name=request.form.get("name"),
                          role=request.form.get("role", "viewer"))
            u.set_password(request.form["password"])
            db.session.add(u)
            db.session.commit()
            record_audit(current_admin(), "team.add", email)
            flash(f"Added {email}.")
        return redirect(url_for("admin.team"))
    return render_template("admin/team.html",
                           rows=AdminUser.query.order_by(AdminUser.created_at).all(),
                           audit=AuditLog.query.order_by(desc(AuditLog.created_at)).limit(40).all())


@admin_bp.route("/team/user/<int:uid>/update", methods=["POST"])
@editor_required
def user_update(uid):
    u = AdminUser.query.get_or_404(uid)
    new_email = request.form.get("email", "").lower().strip()
    new_name = request.form.get("name", "").strip()
    new_role = request.form.get("role", "viewer")
    new_password = request.form.get("password", "").strip()

    if not new_email:
        flash("Email cannot be empty.")
        return redirect(url_for("admin.team"))

    existing = AdminUser.query.filter(AdminUser.email == new_email, AdminUser.id != u.id).first()
    if existing:
        flash("That email address is already in use by another account.")
        return redirect(url_for("admin.team"))

    u.email = new_email
    u.name = new_name or u.name

    if u.id == current_admin().id and new_role != "admin":
        flash("You cannot demote yourself from admin role.")
    else:
        u.role = new_role

    if new_password:
        if len(new_password) < 6:
            flash("New password must be at least 6 characters long.")
            return redirect(url_for("admin.team"))
        u.set_password(new_password)
        record_audit(current_admin(), "team.reset_password", u.email, "Admin reset password")
        flash(f"Updated {u.email} and set a new password.")
    else:
        flash(f"Updated {u.email}.")

    db.session.commit()
    record_audit(current_admin(), "team.update", u.email)
    return redirect(url_for("admin.team"))


@admin_bp.route("/team/user/<int:uid>/delete", methods=["POST"])
@editor_required
def user_delete(uid):
    if uid == current_admin().id:
        flash("You cannot delete your own account.")
        return redirect(url_for("admin.team"))

    u = AdminUser.query.get_or_404(uid)
    email = u.email
    db.session.delete(u)
    db.session.commit()
    record_audit(current_admin(), "team.delete", email)
    flash(f"Deleted {email}.")
    return redirect(url_for("admin.team"))


# ---------------------------------------------------------------- profile / account

@admin_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_admin()
    if request.method == "POST":
        new_email = request.form.get("email", "").lower().strip()
        new_name = request.form.get("name", "").strip()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not new_email:
            flash("Email cannot be empty.")
            return redirect(url_for("admin.profile"))

        existing = AdminUser.query.filter(AdminUser.email == new_email, AdminUser.id != user.id).first()
        if existing:
            flash("That email address is already in use by another user.")
            return redirect(url_for("admin.profile"))

        user.email = new_email
        user.name = new_name or user.name

        # If admin is updating their password
        if new_password:
            if not current_password or not user.check_password(current_password):
                flash("Current password is required and must be correct to set a new password.")
                return redirect(url_for("admin.profile"))
            if len(new_password) < 6:
                flash("New password must be at least 6 characters long.")
                return redirect(url_for("admin.profile"))
            if new_password != confirm_password:
                flash("New passwords do not match.")
                return redirect(url_for("admin.profile"))
            user.set_password(new_password)
            record_audit(user, "profile.password_change", detail="Password updated")
            flash("Password updated successfully.")

        db.session.commit()
        record_audit(user, "profile.update", detail=f"email={user.email}")
        flash("Account details updated successfully.")
        return redirect(url_for("admin.profile"))

    return render_template("admin/profile.html", user=user)
