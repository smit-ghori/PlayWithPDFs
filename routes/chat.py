"""Chat and Announcements blueprint for end-users (PlayWithPDFs).
Provides real-time chat with administrators and department-targeted announcements.
"""

from flask import Blueprint, jsonify, request, session
from extensions import db
from models import ChatMessage, Announcement, User, utcnow
from routes.auth import get_current_user, user_login_required

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.route("/api/messages", methods=["GET"])
@user_login_required
def get_user_messages():
    """Fetch all chat messages between the current user and admin."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    messages = (
        ChatMessage.query.filter_by(user_id=user.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    # Mark incoming admin messages as read
    has_unread = False
    for msg in messages:
        if msg.sender_type == "admin" and not msg.is_read:
            msg.is_read = True
            has_unread = True
    if has_unread:
        db.session.commit()

    return jsonify({
        "success": True,
        "messages": [m.to_dict() for m in messages],
        "user": {
            "id": user.id,
            "name": user.name,
            "department": user.department,
        }
    })


@chat_bp.route("/api/send", methods=["POST"])
@user_login_required
def send_user_message():
    """Send a new message from the user to the admin."""
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or request.form
    text = (data.get("message") or "").strip()

    if not text:
        return jsonify({"error": "Message cannot be empty."}), 400

    if len(text) > 3000:
        return jsonify({"error": "Message is too long (max 3000 characters)."}), 400

    msg = ChatMessage(
        user_id=user.id,
        sender_type="user",
        message=text,
        is_read=False,
    )
    db.session.add(msg)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": msg.to_dict(),
    })


@chat_bp.route("/api/unread-count", methods=["GET"])
def get_unread_count():
    """Get the unread message count and latest message from admin and latest announcement."""
    user = get_current_user()
    chat_count = 0
    latest_chat = None

    if user:
        unread_messages = (
            ChatMessage.query.filter_by(
                user_id=user.id,
                sender_type="admin",
                is_read=False
            )
            .order_by(ChatMessage.created_at.desc())
            .all()
        )
        chat_count = len(unread_messages)
        latest_chat = unread_messages[0].to_dict() if chat_count > 0 else None

    # Get latest active announcement for this user or department
    user_dept = user.department if user else None
    query = Announcement.query.filter_by(is_active=True)
    if user_dept:
        query = query.filter(
            (Announcement.target_department == "ALL") |
            (Announcement.target_department == user_dept)
        )
    else:
        query = query.filter(Announcement.target_department == "ALL")

    latest_announcement_obj = query.order_by(Announcement.created_at.desc()).first()
    latest_announcement = latest_announcement_obj.to_dict() if latest_announcement_obj else None

    return jsonify({
        "count": chat_count,
        "latest": latest_chat,
        "latest_announcement": latest_announcement,
    })


@chat_bp.route("/api/announcements", methods=["GET"])
def get_user_announcements():
    """Get announcements relevant to current user (All departments or user's department)."""
    user = get_current_user()
    user_dept = user.department if user else None

    query = Announcement.query.filter_by(is_active=True)
    if user_dept:
        query = query.filter(
            (Announcement.target_department == "ALL") |
            (Announcement.target_department == user_dept)
        )
    else:
        query = query.filter(Announcement.target_department == "ALL")

    announcements = query.order_by(Announcement.created_at.desc()).limit(20).all()

    return jsonify({
        "success": True,
        "announcements": [a.to_dict() for a in announcements],
        "user_department": user_dept or "Guest",
    })
