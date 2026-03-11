from flask import Blueprint, render_template, request

compress_bp = Blueprint("compress", __name__)


@compress_bp.route("/compress", methods=["GET", "POST"])
def compress():

    if request.method == "POST":
        # compression logic will be added later
        pass

    return render_template("compress.html")