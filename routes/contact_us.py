from flask import Blueprint, render_template, request
from flask_mail import Message
from extensions import mail

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
            sender="smitghori83@gmail.com",
            recipients=["smitghori83@gmail.com"],
        )

        msg.body = f"""

Name: {name}

Email: {email}

Subject: {subject}

Message:
{message}

"""

        mail.send(msg)

        return render_template("contact_us.html", success=True)

    return render_template("contact_us.html")
