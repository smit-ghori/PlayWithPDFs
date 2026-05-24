from flask import Blueprint, redirect, render_template, request, url_for, current_app
from flask_mail import Message
from extensions import mail
import os
import threading

contact_us_bp = Blueprint("contact_us", __name__)


def send_email_async(app, msg):
    """Send email asynchronously to avoid blocking the request"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Error sending email: {e}")


@contact_us_bp.route("/contact_us", methods=["GET", "POST"])
def contact_us():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")

        # EMAIL SEND (ASYNC - Non-blocking)
        mail_username = os.environ.get("MAIL_USERNAME")
        if mail_username:
            msg = Message(
                subject=f"PlayWithPDFs Contact: {subject}",
                sender=mail_username,  # your Gmail account
                recipients=[mail_username],  # must be a list
                reply_to=email,  # user's email, so reply goes to them
            )

            msg.body = f"""

Name: {name}

Email: {email}

Subject: {subject}

Message:
{message}

"""

            # Send email in background thread
            thread = threading.Thread(target=send_email_async, args=(current_app._get_current_object(), msg))
            thread.daemon = True
            thread.start()

        return redirect(url_for("contact_us.contact_us", success="1"))

    success = request.args.get("success") == "1"

    return render_template("contact_us.html", success=success)
