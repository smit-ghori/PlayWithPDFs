"""Automatic per-tool tracking and kill-switches.

Nothing here requires editing the 34 route files. It hooks Flask's
before_request / after_request and uses the blueprint name as the tool name.
"""

import time
import hashlib
import os
from flask import request, g, render_template, jsonify, flash, redirect
from extensions import db
from models import ToolEvent, ToolConfig

# Blueprints that are not tools and should not be tracked or blocked.
SKIP = {"admin", "home", "about", "static", None}

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

        cfg = get_flags().get(tool)
        if cfg and not cfg["enabled"]:
            note = cfg["note"] or "This tool is temporarily unavailable."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", ""):
                return jsonify({"error": note, "tool": tool, "disabled": True}), 503
            return render_template(
                "admin/tool_disabled.html",
                tool=tool, note=note,
            ), 503

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
    for name in app.blueprints:
        if name in SKIP:
            continue
        if not ToolConfig.query.filter_by(tool=name).first():
            db.session.add(ToolConfig(tool=name, label=name.replace("_", " ").title()))
            created += 1
    db.session.commit()
    return created
