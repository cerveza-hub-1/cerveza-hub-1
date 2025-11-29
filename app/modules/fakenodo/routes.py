from flask import jsonify, render_template, request

from app.modules.fakenodo import fakenodo_bp
from app.modules.fakenodo.services import FakenodoService

service = FakenodoService()


@fakenodo_bp.route("/fakenodo", methods=["GET"])
def index():
    return render_template("fakenodo/index.html")


@fakenodo_bp.route("/test", methods=["GET"])
def fakenodo_test() -> dict:
    service = FakenodoService()
    return service.test_full_connection()


@fakenodo_bp.route("/api/records", methods=["POST"])
def create_record():
    data = request.get_json()
    record = service.create_record(data.get("meta", {}))
    return jsonify(record), 201


@fakenodo_bp.route("/api/records/<record_id>/actions/publish", methods=["POST"])
def publish_record(record_id):
    data = request.get_json()
    files = data.get("files", [])
    version = service.publish_record(record_id, files)
    return jsonify(version), 202


@fakenodo_bp.route("/api/records/<record_id>/versions", methods=["GET"])
def list_versions(record_id):
    versions = service.list_versions(record_id)
    return jsonify(versions), 200


@fakenodo_bp.route("/api/records/<record_id>/files", methods=["POST"])
def upload_files(record_id):
    return jsonify({"message": "File uploaded (simulated)", "record_id": record_id}), 201


@fakenodo_bp.route("/api/records/<record_id>", methods=["DELETE"])
def delete_record(record_id):
    return jsonify({"message": "Record deleted (simulated)", "record_id": record_id}), 200
