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
                   session, flash, Response, abort, current_app, jsonify)
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask_mail import Message
from sqlalchemy import func, desc

from extensions import db, mail
from models import (AdminUser, User, ToolConfig, ToolEvent, ContactMessage,
                    AuditLog, ChatMessage, Announcement, Department, ToolPermission,
                    get_department_names, seed_departments, DEPARTMENTS, record_audit, utcnow)
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
        user = current_admin()
        if not user or user.role != "admin":
            msg = "Access Denied: You are signed in as a Viewer and are not permitted to access or modify this section. Only Administrators have permission."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", ""):
                return jsonify({"error": msg, "forbidden": True}), 403
            flash(msg, "error")
            return redirect(request.referrer or url_for("admin.dashboard"))
        return view(*a, **kw)
    return wrapper


@admin_bp.app_errorhandler(403)
def forbidden_error(e):
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", ""):
        return jsonify({
            "error": "You are signed in as a Viewer and are not permitted to perform this action.",
            "forbidden": True
        }), 403
    return render_template("admin/403.html"), 403


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


# ---------------------------------------------------------------- tool access control (department & user)

@admin_bp.route("/tools/permissions")
@login_required
def tools_permissions_matrix():
    tools = ToolConfig.query.order_by(ToolConfig.tool.asc()).all()
    departments = Department.query.filter_by(is_active=True).order_by(Department.name.asc()).all()
    
    # Map department permissions: {(tool, dept_name): perm_object}
    all_dept_perms = ToolPermission.query.filter_by(target_type="department").all()
    dept_perms_map = {(p.tool, p.target_id): p for p in all_dept_perms}

    # User overrides
    user_perms = ToolPermission.query.filter_by(target_type="user").order_by(desc(ToolPermission.updated_at)).all()
    user_map = {str(u.id): u for u in User.query.all()}

    return render_template(
        "admin/tools_permissions_matrix.html",
        tools=tools,
        departments=departments,
        dept_perms_map=dept_perms_map,
        user_perms=user_perms,
        user_map=user_map,
    )


@admin_bp.route("/tools/<tool>/permissions", methods=["GET"])
@login_required
def tool_granular_permissions(tool):
    tool_cfg = ToolConfig.query.filter_by(tool=tool).first_or_404()
    departments = Department.query.filter_by(is_active=True).order_by(Department.name.asc()).all()
    all_users = User.query.order_by(User.name.asc()).all()

    # Department permissions for this tool
    dept_perms = {p.target_id: p for p in ToolPermission.query.filter_by(tool=tool, target_type="department").all()}

    # User overrides for this tool
    user_perms = ToolPermission.query.filter_by(tool=tool, target_type="user").order_by(desc(ToolPermission.updated_at)).all()
    user_map = {str(u.id): u for u in all_users}

    return render_template(
        "admin/tool_permissions.html",
        tool=tool_cfg,
        departments=departments,
        dept_perms=dept_perms,
        user_perms=user_perms,
        users=all_users,
        user_map=user_map,
    )


@admin_bp.route("/tools/<tool>/permissions/dept-toggle", methods=["POST"])
@editor_required
def tool_dept_toggle(tool):
    dept_name = request.form.get("department", "").strip()
    state = request.form.get("state", "").strip()  # 'inherit' | 'enabled' | 'disabled'
    note = request.form.get("note", "").strip()

    perm = ToolPermission.query.filter_by(tool=tool, target_type="department", target_id=dept_name).first()

    if state == "inherit":
        if perm:
            db.session.delete(perm)
            db.session.commit()
            flash(f"Reset {tool} for department '{dept_name}' to inherit global setting.")
    elif state in ("enabled", "disabled"):
        is_en = (state == "enabled")
        if not perm:
            perm = ToolPermission(
                tool=tool,
                target_type="department",
                target_id=dept_name,
                is_enabled=is_en,
                note=note or None,
            )
            db.session.add(perm)
        else:
            perm.is_enabled = is_en
            if note:
                perm.note = note
        db.session.commit()
        flash(f"Department '{dept_name}' is now {'ENABLED' if is_en else 'DISABLED'} for {tool}.")

    invalidate_flags()
    record_audit(current_admin(), "tool.dept_permission", tool, f"dept={dept_name}, state={state}")
    return redirect(request.referrer or url_for('admin.tool_granular_permissions', tool=tool))


@admin_bp.route("/tools/<tool>/permissions/user-override", methods=["POST"])
@editor_required
def tool_user_override(tool):
    user_id = request.form.get("user_id", "").strip()
    is_enabled = request.form.get("is_enabled") == "1"
    note = request.form.get("note", "").strip()

    if not user_id:
        flash("Please select a user.", "error")
        return redirect(request.referrer or url_for('admin.tool_granular_permissions', tool=tool))

    user = User.query.get_or_404(int(user_id))
    perm = ToolPermission.query.filter_by(tool=tool, target_type="user", target_id=str(user.id)).first()

    if not perm:
        perm = ToolPermission(
            tool=tool,
            target_type="user",
            target_id=str(user.id),
            is_enabled=is_enabled,
            note=note or None,
        )
        db.session.add(perm)
    else:
        perm.is_enabled = is_enabled
        if note:
            perm.note = note

    db.session.commit()
    invalidate_flags()
    status_label = "ENABLED (Allowed)" if is_enabled else "DISABLED (Restricted)"
    record_audit(current_admin(), "tool.user_override", tool, f"user={user.email}, status={status_label}")
    flash(f"Tool {tool} has been set to {status_label} for {user.name} ({user.email}).")
    return redirect(request.referrer or url_for('admin.tool_granular_permissions', tool=tool))


@admin_bp.route("/tools/permissions/delete/<int:pid>", methods=["POST"])
@editor_required
def tool_permission_delete(pid):
    perm = ToolPermission.query.get_or_404(pid)
    tool = perm.tool
    target = f"{perm.target_type}:{perm.target_id}"
    db.session.delete(perm)
    db.session.commit()
    invalidate_flags()
    record_audit(current_admin(), "tool.permission_deleted", tool, target)
    flash(f"Removed custom override for {target}.")
    return redirect(request.referrer or url_for('admin.tools'))


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


# ---------------------------------------------------------------- end-user management

@admin_bp.route("/users")
@login_required
def users_list():
    dept_filter = request.args.get("department", "").strip()
    search = request.args.get("q", "").strip()
    available_depts = get_department_names()

    query = User.query
    if dept_filter and dept_filter != "ALL":
        query = query.filter(User.department == dept_filter)
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )

    users = query.order_by(desc(User.created_at)).all()

    # Department statistics
    dept_stats = {}
    for d in available_depts:
        dept_stats[d] = User.query.filter_by(department=d).count()
    total_users = User.query.count()

    # User-specific tool overrides count
    user_overrides_counts = {}
    all_user_perms = ToolPermission.query.filter_by(target_type="user").all()
    for p in all_user_perms:
        user_overrides_counts[p.target_id] = user_overrides_counts.get(p.target_id, 0) + 1

    return render_template(
        "admin/users.html",
        users=users,
        departments=available_depts,
        selected_dept=dept_filter,
        search=search,
        dept_stats=dept_stats,
        total_users=total_users,
        user_overrides_counts=user_overrides_counts,
    )


@admin_bp.route("/users/<int:uid>/update", methods=["POST"])
@editor_required
def user_modify(uid):
    user = User.query.get_or_404(uid)
    new_dept = request.form.get("department", "").strip()
    new_name = request.form.get("name", "").strip()
    new_active = request.form.get("is_active") == "1"
    new_password = request.form.get("password", "").strip()

    available_depts = get_department_names()
    if new_dept in available_depts:
        user.department = new_dept
    if new_name:
        user.name = new_name
    user.is_active = new_active

    if new_password:
        if len(new_password) < 6:
            flash("New password must be at least 6 characters.", "error")
            return redirect(url_for("admin.users_list"))
        user.set_password(new_password)
        record_audit(current_admin(), "user.reset_password", user.email, "Admin reset end-user password")
        flash(f"Updated {user.email} and set new password.")
    else:
        flash(f"Updated {user.email}.")

    db.session.commit()
    record_audit(current_admin(), "user.update", user.email, f"dept={user.department}, active={user.is_active}")
    return redirect(url_for("admin.users_list"))


@admin_bp.route("/users/<int:uid>/delete", methods=["POST"])
@editor_required
def user_remove(uid):
    user = User.query.get_or_404(uid)
    email = user.email
    # Remove user-level tool permissions
    ToolPermission.query.filter_by(target_type="user", target_id=str(user.id)).delete()
    db.session.delete(user)
    db.session.commit()
    record_audit(current_admin(), "user.delete", email)
    flash(f"Deleted user {email}.")
    return redirect(url_for("admin.users_list"))


# ---------------------------------------------------------------- department management

@admin_bp.route("/departments")
@login_required
def departments_list():
    depts = Department.query.order_by(Department.name.asc()).all()
    user_counts = {}
    for d in depts:
        user_counts[d.name] = User.query.filter_by(department=d.name).count()

    total_depts = len(depts)
    total_users = User.query.count()

    # Department tool restrictions summary
    dept_restrictions = {}
    for p in ToolPermission.query.filter_by(target_type="department", is_enabled=False).all():
        dept_restrictions[p.target_id] = dept_restrictions.get(p.target_id, 0) + 1

    return render_template(
        "admin/departments.html",
        departments=depts,
        user_counts=user_counts,
        total_depts=total_depts,
        total_users=total_users,
        dept_restrictions=dept_restrictions,
    )


@admin_bp.route("/departments/create", methods=["POST"])
@editor_required
def department_create():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not name or len(name) < 2:
        flash("Department name must be at least 2 characters.", "error")
        return redirect(url_for("admin.departments_list"))

    existing = Department.query.filter(func.lower(Department.name) == func.lower(name)).first()
    if existing:
        flash(f"Department '{name}' already exists.", "error")
        return redirect(url_for("admin.departments_list"))

    dept = Department(name=name, description=description, is_active=True)
    db.session.add(dept)
    db.session.commit()
    record_audit(current_admin(), "department.create", name, description)
    flash(f"Department '{name}' added successfully.")
    return redirect(url_for("admin.departments_list"))


@admin_bp.route("/departments/<int:did>/update", methods=["POST"])
@editor_required
def department_update(did):
    dept = Department.query.get_or_404(did)
    old_name = dept.name
    new_name = request.form.get("name", "").strip()
    new_desc = request.form.get("description", "").strip()
    new_active = request.form.get("is_active") == "1"

    if not new_name or len(new_name) < 2:
        flash("Department name must be at least 2 characters.", "error")
        return redirect(url_for("admin.departments_list"))

    if new_name.lower() != old_name.lower():
        existing = Department.query.filter(func.lower(Department.name) == func.lower(new_name), Department.id != did).first()
        if existing:
            flash(f"A department named '{new_name}' already exists.", "error")
            return redirect(url_for("admin.departments_list"))

        # Reassign users and tool permissions to the new department name
        User.query.filter_by(department=old_name).update({"department": new_name})
        ToolPermission.query.filter_by(target_type="department", target_id=old_name).update({"target_id": new_name})
        Announcement.query.filter_by(target_department=old_name).update({"target_department": new_name})

    dept.name = new_name
    dept.description = new_desc
    dept.is_active = new_active
    db.session.commit()
    record_audit(current_admin(), "department.update", new_name, f"old_name={old_name}, active={new_active}")
    flash(f"Department '{new_name}' updated successfully.")
    return redirect(url_for("admin.departments_list"))


@admin_bp.route("/departments/<int:did>/delete", methods=["POST"])
@editor_required
def department_delete(did):
    dept = Department.query.get_or_404(did)
    name = dept.name
    user_count = User.query.filter_by(department=name).count()
    if user_count > 0:
        User.query.filter_by(department=name).update({"department": "General / Other"})

    # Clean up associated department permissions
    ToolPermission.query.filter_by(target_type="department", target_id=name).delete()
    db.session.delete(dept)
    db.session.commit()
    record_audit(current_admin(), "department.delete", name, f"reassigned_{user_count}_users")
    flash(f"Department '{name}' deleted. {user_count} users moved to General / Other.")
    return redirect(url_for("admin.departments_list"))


# ---------------------------------------------------------------- support chat

@admin_bp.route("/chat")
@login_required
def chat_dashboard():
    all_users = User.query.order_by(desc(User.created_at)).all()
    user_threads = []
    for u in all_users:
        last_msg = ChatMessage.query.filter_by(user_id=u.id).order_by(desc(ChatMessage.created_at)).first()
        unread_count = ChatMessage.query.filter_by(user_id=u.id, sender_type="user", is_read=False).count()
        user_threads.append({
            "user": u,
            "last_message": last_msg,
            "unread_count": unread_count,
        })

    user_threads.sort(
        key=lambda x: (
            x["unread_count"] > 0,
            x["last_message"].created_at if x["last_message"] else x["user"].created_at
        ),
        reverse=True
    )

    selected_uid = request.args.get("user_id", type=int)
    if not selected_uid and user_threads:
        selected_uid = user_threads[0]["user"].id

    return render_template(
        "admin/chat.html",
        threads=user_threads,
        selected_uid=selected_uid,
    )


@admin_bp.route("/chat/api/thread/<int:uid>", methods=["GET"])
@login_required
def chat_get_thread(uid):
    user = User.query.get_or_404(uid)
    messages = (
        ChatMessage.query.filter_by(user_id=user.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    has_unread = False
    for m in messages:
        if m.sender_type == "user" and not m.is_read:
            m.is_read = True
            has_unread = True
    if has_unread:
        db.session.commit()

    return jsonify({
        "success": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "department": user.department,
            "is_active": user.is_active,
        },
        "messages": [m.to_dict() for m in messages],
    })


@admin_bp.route("/chat/api/reply/<int:uid>", methods=["POST"])
@login_required
def chat_reply_thread(uid):
    user = User.query.get_or_404(uid)
    admin = current_admin()
    data = request.get_json(silent=True) or request.form
    text = (data.get("message") or "").strip()

    if not text:
        return jsonify({"error": "Message cannot be empty."}), 400

    msg = ChatMessage(
        user_id=user.id,
        sender_type="admin",
        admin_id=admin.id,
        message=text,
        is_read=False,
    )
    db.session.add(msg)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": msg.to_dict(),
    })


@admin_bp.route("/chat/api/unread-total", methods=["GET"])
@login_required
def chat_unread_total():
    count = ChatMessage.query.filter_by(sender_type="user", is_read=False).count()
    return jsonify({"count": count})


# ---------------------------------------------------------------- announcements

@admin_bp.route("/announcements")
@login_required
def announcements_list():
    items = Announcement.query.order_by(desc(Announcement.created_at)).all()
    return render_template(
        "admin/announcements.html",
        announcements=items,
        departments=get_department_names(),
    )


@admin_bp.route("/announcements/create", methods=["POST"])
@editor_required
def announcement_create():
    admin = current_admin()
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    target_dept = request.form.get("target_department", "ALL").strip()
    available_depts = get_department_names()

    if not title or not content:
        flash("Title and content are required.", "error")
        return redirect(url_for("admin.announcements_list"))

    if target_dept != "ALL" and target_dept not in available_depts:
        target_dept = "ALL"

    ann = Announcement(
        title=title,
        content=content,
        target_department=target_dept,
        admin_id=admin.id,
        is_active=True,
    )
    db.session.add(ann)
    db.session.commit()
    record_audit(admin, "announcement.create", title, f"target={target_dept}")
    flash(f"Announcement '{title}' published successfully.")
    return redirect(url_for("admin.announcements_list"))


@admin_bp.route("/announcements/<int:aid>/toggle", methods=["POST"])
@editor_required
def announcement_toggle(aid):
    ann = Announcement.query.get_or_404(aid)
    ann.is_active = not ann.is_active
    db.session.commit()
    state = "activated" if ann.is_active else "deactivated"
    record_audit(current_admin(), "announcement.toggle", ann.title, f"state={state}")
    flash(f"Announcement '{ann.title}' {state}.")
    return redirect(url_for("admin.announcements_list"))


@admin_bp.route("/announcements/<int:aid>/delete", methods=["POST"])
@editor_required
def announcement_delete(aid):
    ann = Announcement.query.get_or_404(aid)
    title = ann.title
    db.session.delete(ann)
    db.session.commit()
    record_audit(current_admin(), "announcement.delete", title)
    flash(f"Deleted announcement '{title}'.")
    return redirect(url_for("admin.announcements_list"))
