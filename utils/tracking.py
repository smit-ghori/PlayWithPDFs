"""Automatic per-tool tracking and kill-switches.

Nothing here requires editing the 34 route files. It hooks Flask's
before_request / after_request and uses the blueprint name as the tool name.
"""

import time
import hashlib
import os
from flask import request, g, render_template, jsonify, flash, redirect, session, url_for
from extensions import db
from models import ToolEvent, ToolConfig, User, ToolPermission

# Blueprints that are not tools and should not be tracked or blocked.
SKIP = {"admin", "home", "about", "static", "auth", "contact_us", "chat", None}

_flag_cache = {"at": 0.0, "data": {}}
_FLAG_TTL = 20  # seconds


def _visitor_hash():
    salt = os.environ.get("SECRET_KEY", "salt")
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
    ip = ip.split(",")[0].strip()
    return hashlib.sha256((salt + ip).encode()).hexdigest()[:32]


def get_flags():
    """Cached {tool: ToolConfig-ish dict}. Avoids a DB hit per request."""
    now = time.time()
    if now - _flag_cache["at"] > _FLAG_TTL:
        try:
            rows = ToolConfig.query.all()
            _flag_cache["data"] = {
                r.tool: {"enabled": r.enabled, "note": r.maintenance_note,
                         "max_file_mb": r.max_file_mb, "max_files": r.max_files}
                for r in rows
            }
            _flag_cache["at"] = now
        except Exception:
            pass  # DB down: fail open, site keeps working
    return _flag_cache["data"]


def invalidate_flags():
    _flag_cache["at"] = 0.0


def _resolve_tool_access(tool, user, cfg):
    """
    Check if a tool is accessible according to the 3-tier hierarchy:
    1. User level override (highest priority)
    2. Department level override (middle priority)
    3. Global tool setting (base level)
    Returns (is_allowed: bool, note: str or None)
    """
    tool_title = tool.replace("_", " ").title()

    # 1. User-level override
    if user:
        try:
            user_perm = ToolPermission.query.filter_by(
                tool=tool,
                target_type="user",
                target_id=str(user.id)
            ).first()
            if user_perm is not None:
                if not user_perm.is_enabled:
                    note = user_perm.note or f"Access to {tool_title} has been disabled specifically for your account by administration."
                    return False, note
                else:
                    # Explicit user grant overrides department/global restriction
                    return True, None
        except Exception:
            pass

    # 2. Department-level override
    if user and user.department:
        try:
            dept_perm = ToolPermission.query.filter_by(
                tool=tool,
                target_type="department",
                target_id=user.department
            ).first()
            if dept_perm is not None:
                if not dept_perm.is_enabled:
                    note = dept_perm.note or f"Access to {tool_title} has been restricted for your department ({user.department}) by administration."
                    return False, note
                else:
                    return True, None
        except Exception:
            pass

    # 3. Global tool kill switch
    if cfg and not cfg.get("enabled", True):
        note = cfg.get("note") or f"{tool_title} is temporarily paused for maintenance."
        return False, note

    return True, None


def init_tracking(app):

    @app.context_processor
    def _inject_tool_config():
        tool = request.blueprint
        if tool and tool not in SKIP:
            cfg = get_flags().get(tool)
            return {"current_tool_config": cfg}
        return {"current_tool_config": None}

    @app.before_request
    def _start():
        g._t0 = time.perf_counter()
        tool = request.blueprint
        if tool in SKIP:
            return None

        # -------------------------------------------------------------
        # Enforce user authentication for all operational PDF tools
        # -------------------------------------------------------------
        user_id = session.get("user_id")
        user = None
        if user_id:
            try:
                user = User.query.get(user_id)
            except Exception:
                user = None

        if not user or not user.is_active:
            if user_id and not user:
                # User id in session is invalid or user was removed
                session.pop("user_id", None)
            elif user and not user.is_active:
                session.pop("user_id", None)
                flash("Your account has been deactivated. Please contact support.", "error")
                return redirect(url_for("auth.login"))

            msg = "Please log in or create a free account to use this tool."
            next_target = request.full_path if request.query_string else request.path

            # Return JSON 401 if requested via AJAX or API fetch
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", ""):
                return jsonify({
                    "error": msg,
                    "login_required": True,
                    "redirect": url_for("auth.login", next=next_target)
                }), 401

            flash(msg, "warning")
            return redirect(url_for("auth.login", next=next_target))

        cfg = get_flags().get(tool)
        is_allowed, block_note = _resolve_tool_access(tool, user, cfg)
        if not is_allowed:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", ""):
                return jsonify({"error": block_note, "tool": tool, "disabled": True}), 403
            return render_template(
                "admin/tool_disabled.html",
                tool=tool, note=block_note,
            ), 403

        if request.method == "POST" and cfg:
            max_limit = cfg.get("max_files") or 999
            non_empty_files = 0
            if request.files:
                for k in request.files:
                    for f in request.files.getlist(k):
                        if f and getattr(f, "filename", ""):
                            non_empty_files += 1

            if non_empty_files > max_limit:
                msg = f"Maximum file limit is {max_limit}. You selected {non_empty_files} files. Please upload up to {max_limit} files only."
                if request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", ""):
                    return jsonify({
                        "error": msg,
                        "max_files": max_limit,
                        "uploaded": non_empty_files
                    }), 400

                flash(msg, "error")
                return redirect(request.referrer or request.url)

    @app.after_request
    def _finish(response):
        tool = request.blueprint
        if tool in SKIP:
            return response
        try:
            in_bytes = request.content_length or 0
            out_bytes = response.calculate_content_length() or 0
            db.session.add(ToolEvent(
                tool=tool,
                endpoint=request.endpoint,
                method=request.method,
                status_code=response.status_code,
                ok=response.status_code < 400,
                duration_ms=int((time.perf_counter() - getattr(g, "_t0", 0)) * 1000),
                input_bytes=in_bytes,
                output_bytes=out_bytes,
                file_count=sum(len(v) for v in request.files.listvalues()) if request.files else 0,
                visitor=_visitor_hash(),
                user_agent=(request.user_agent.string or "")[:255],
            ))
            db.session.commit()
        except Exception:
            db.session.rollback()   # never break a download over analytics
        return response

    @app.errorhandler(Exception)
    def _log_error(e):
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return e
        try:
            db.session.rollback()
            db.session.add(ToolEvent(
                tool=request.blueprint or "unknown",
                endpoint=request.endpoint, method=request.method,
                status_code=500, ok=False,
                duration_ms=int((time.perf_counter() - getattr(g, "_t0", 0)) * 1000),
                visitor=_visitor_hash(),
                error_text=f"{type(e).__name__}: {e}"[:4000],
            ))
            db.session.commit()
        except Exception:
            db.session.rollback()
        raise e


def seed_tools(app):
    """Create a ToolConfig row for every registered blueprint."""
    created = 0
    try:
        existing = {r.tool for r in ToolConfig.query.all()}
        for name in app.blueprints:
            if name in SKIP or name in existing:
                continue
            db.session.add(ToolConfig(tool=name, label=name.replace("_", " ").title()))
            created += 1
        if created > 0:
            db.session.commit()
    except Exception as e:
        db.session.rollback()
    return created
