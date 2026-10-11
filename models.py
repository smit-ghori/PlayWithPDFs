"""Database models for PlayWithPDFs admin panel (PostgreSQL)."""

from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class AdminUser(db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(190), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="admin")   # admin | viewer
    is_active = db.Column(db.Boolean, default=True)
    last_login_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


DEPARTMENTS = [
    "Engineering & IT",
    "Operations",
    "Finance & Accounting",
    "Human Resources (HR)",
    "Marketing & Sales",
    "Legal & Compliance",
    "Product & Design",
    "Customer Support",
    "General / Other",
]


class User(db.Model):
    """End-user account for PlayWithPDFs web application."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(190), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(80), nullable=False, default="General / Other", index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


class ToolConfig(db.Model):
    """One row per tool. Lets you rename, disable or throttle a tool
    from the panel without a redeploy."""
    __tablename__ = "tool_configs"

    id = db.Column(db.Integer, primary_key=True)
    tool = db.Column(db.String(60), unique=True, nullable=False, index=True)
    label = db.Column(db.String(120))
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    maintenance_note = db.Column(db.String(255))
    max_file_mb = db.Column(db.Integer, default=50)
    max_files = db.Column(db.Integer, default=20)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ToolEvent(db.Model):
    """One row per tool request. This is the analytics + error table."""
    __tablename__ = "tool_events"

    id = db.Column(db.BigInteger, primary_key=True)
    tool = db.Column(db.String(60), index=True, nullable=False)
    endpoint = db.Column(db.String(120))
    method = db.Column(db.String(8))
    status_code = db.Column(db.Integer, index=True)
    ok = db.Column(db.Boolean, default=True, index=True)
    duration_ms = db.Column(db.Integer)
    input_bytes = db.Column(db.BigInteger, default=0)
    output_bytes = db.Column(db.BigInteger, default=0)
    file_count = db.Column(db.Integer, default=0)
    visitor = db.Column(db.String(64), index=True)   # hashed IP, not the IP
    user_agent = db.Column(db.String(255))
    error_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, index=True)


class ContactMessage(db.Model):
    """Replaces the fire-and-forget email in routes/contact_us.py."""
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(190), index=True)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="new", index=True)  # new|open|closed
    email_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, index=True)
    handled_at = db.Column(db.DateTime(timezone=True))


class AuditLog(db.Model):
    """Who changed what in the panel."""
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin_users.id"))
    admin_email = db.Column(db.String(190))
    action = db.Column(db.String(80), nullable=False)
    target = db.Column(db.String(120))
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, index=True)


def record_audit(admin, action, target=None, detail=None):
    db.session.add(AuditLog(
        admin_id=getattr(admin, "id", None),
        admin_email=getattr(admin, "email", "system"),
        action=action, target=target, detail=detail,
    ))
    db.session.commit()


class ChatMessage(db.Model):
    """Direct chat messages between a specific user and the admin support team."""
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_type = db.Column(db.String(20), nullable=False, index=True)  # 'user' | 'admin'
    admin_id = db.Column(db.Integer, db.ForeignKey("admin_users.id"), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, index=True)

    user = db.relationship("User", backref=db.backref("messages", lazy="dynamic", cascade="all, delete-orphan"))
    admin = db.relationship("AdminUser", backref=db.backref("sent_replies", lazy="dynamic"))

    def to_dict(self):
        admin_name = None
        if self.admin:
            admin_name = self.admin.name or self.admin.email
        return {
            "id": self.id,
            "user_id": self.user_id,
            "sender_type": self.sender_type,
            "sender_name": admin_name if self.sender_type == "admin" else (self.user.name if self.user else "User"),
            "admin_id": self.admin_id,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "formatted_time": self.created_at.strftime("%b %d, %I:%M %p") if self.created_at else "",
        }


class Announcement(db.Model):
    """Broadcast announcements from admins, targeted department-wise or to all."""
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    target_department = db.Column(db.String(80), default="ALL", nullable=False, index=True)  # 'ALL' or department name
    admin_id = db.Column(db.Integer, db.ForeignKey("admin_users.id"), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, index=True)

    admin = db.relationship("AdminUser", backref=db.backref("announcements", lazy="dynamic"))

    def to_dict(self):
        admin_name = None
        if self.admin:
            admin_name = self.admin.name or self.admin.email
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "target_department": self.target_department,
            "admin_name": admin_name or "Administration",
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "formatted_time": self.created_at.strftime("%b %d, %Y %I:%M %p") if self.created_at else "",
        }
