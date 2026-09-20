from flask import Blueprint, render_template, request

home_bp = Blueprint("home", __name__)

@home_bp.route("/")
def home():
    initial_query = request.args.get("q", "").strip()
    return render_template("index.html", initial_query=initial_query)