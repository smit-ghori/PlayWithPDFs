from flask import Blueprint, render_template

add_watermark_bp = Blueprint("add_watermark", __name__)

@add_watermark_bp.route("/add_watermark")
def add_watermark():
    return render_template("add_watermark.html")