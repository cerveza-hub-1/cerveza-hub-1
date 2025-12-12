from flask import render_template

from app.modules.csvmodel import csvmodel_bp


@csvmodel_bp.route("/csvmodel", methods=["GET"])
def index():
    return render_template("csvmodel/index.html")
