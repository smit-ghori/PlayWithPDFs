from flask import Blueprint, redirect, render_template, request, url_for
from flask_mail import Message
from extensions import mail
import os

contact_us_bp = Blueprint("contact_us", __name__)


@contact_us_bp.route("/contact_us", methods=["GET", "POST"])
def contact_us():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")

        # EMAIL SEND

        msg = Message(
            subject=f"PlayWithPDFs Contact: {subject}",
            sender=os.environ.get("MAIL_USERNAME"),  # your Gmail account
            recipients=[os.environ.get("MAIL_USERNAME")],  # must be a list
            reply_to=email,  # user’s email, so reply goes to them
        )

        msg.body = f"""

Name: {name}

Email: {email}

Subject: {subject}

Message:
{message}

"""

        mail.send(msg)

        return redirect(url_for("contact_us.contact_us", success="1"))

    success = request.args.get("success") == "1"

    return render_template("contact_us.html", success=success)
