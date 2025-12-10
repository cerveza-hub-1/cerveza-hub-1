from flask import jsonify, render_template, request

from app.modules.fakenodo import fakenodo_bp
from app.modules.fakenodo.services import FakenodoService

service = FakenodoService()


@fakenodo_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@fakenodo_bp.route("/api/records", methods=["POST"])
def create_record():
    data = request.get_json()
    record = service.create_record(data.get("meta", {}))
    return jsonify(record), 201


@fakenodo_bp.route("/api/records/<record_id>", methods=["GET"])
def get_record(record_id):
    try:
        record = service.get_record(record_id)
        return jsonify(record), 200
    except KeyError as e:
        return jsonify({"error": str(e)}), 404


@fakenodo_bp.route("/api/records/<record_id>/actions/publish", methods=["POST"])
def publish_record(record_id):
    data = request.get_json() or {}
    files = data.get("files", [])
    try:
        version = service.publish_record(record_id, files)
        return jsonify(version), 202
    except KeyError as e:
        return jsonify({"error": str(e)}), 404


@fakenodo_bp.route("/api/records/<record_id>/files", methods=["POST"])
def upload_files(record_id):
    if "file" in request.files:
        uploaded = request.files["file"]
        filename = request.form.get("name", uploaded.filename)
        files = [filename]
    else:
        data = request.get_json() or {}
        files = data.get("files", [])

    return jsonify({
        "record_id": record_id,
        "message": "Files uploaded (simulated)",
        "files": files,
    }), 201


@fakenodo_bp.route("/api/records", methods=["GET"])
def list_records():
    return jsonify({"records": service.list_all()}), 200


@fakenodo_bp.route("/records/<record_id>", methods=["GET"])
def view_record_page(record_id):
    """
    Public-facing HTML page for viewing a Fakenodo record.
    """
    try:
        record = service.get_record(record_id)
        return render_template(
            "record_view.html",
            record=record,
            record_url=request.url
        )
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
