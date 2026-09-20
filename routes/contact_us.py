from flask import Blueprint, redirect, render_template, request, url_for, current_app
from flask_mail import Message
from extensions import mail, db
from models import ContactMessage
import os
import threading

contact_us_bp = Blueprint("contact_us", __name__)


def send_email_async(app, msg, message_id):
    """Send email asynchronously and update email_sent status in DB."""
    with app.app_context():
        try:
            mail.send(msg)
            row = ContactMessage.query.get(message_id)
            if row:
                row.email_sent = True
                db.session.commit()
        except Exception as e:
            print(f"Error sending email: {e}")


@contact_us_bp.route("/contact_us", methods=["GET", "POST"])
def contact_us():
    if request.method == "POST":
        name = (request.form.get("name") or "")[:120]
        email = (request.form.get("email") or "")[:190]
        subject = (request.form.get("subject") or "")[:200]
        message_text = request.form.get("message") or ""

        # Save to database first so inquiry is never lost
        row = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message_text,
        )
        try:
            db.session.add(row)
            db.session.commit()
            msg_id = row.id
        except Exception as e:
            db.session.rollback()
            print(f"Error saving contact message: {e}")
            msg_id = None

        # Send notification email if configured
        mail_username = os.environ.get("MAIL_USERNAME")
        if mail_username and msg_id:
            msg = Message(
                subject=f"[PlayWithPDFs] {subject or 'New message'}",
                sender=mail_username,
                recipients=[mail_username],
                reply_to=email,
            )
            msg.body = f"From: {name} <{email}>\nSubject: {subject}\n\n{message_text}"

            thread = threading.Thread(
                target=send_email_async,
                args=(current_app._get_current_object(), msg, msg_id),
            )
            thread.daemon = True
            thread.start()

        return redirect(url_for("contact_us.contact_us", success="1"))

    success = request.args.get("success") == "1"
    return render_template("contact_us.html", success=success)
