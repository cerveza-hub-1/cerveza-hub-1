from flask import Blueprint, request, jsonify
from doi import new_id, root_doi, versioned_doi
import time

fakenodo_bp = Blueprint("fakenodo", __name__, url_prefix="/fakenodo")

depositions = {}
records = {}


@fakenodo_bp.route("/depositions", methods=["POST"])
def create_deposition():
    """
    Crear una deposition (borrador).
    """
    data = request.json or {}
    metadata = data.get("metadata", {})
    files = data.get("files", [])

    dep_id = new_id()
    doi_root = root_doi(dep_id)

    deposition = {
        "id": dep_id,
        "created_at": time.time(),
        "metadata": metadata,
        "files": files,
        "doi_root": doi_root,
        "published": False,
    }
    depositions[dep_id] = deposition
    return jsonify(deposition), 201


@fakenodo_bp.route("/depositions/<dep_id>/metadata", methods=["PATCH"])
def update_deposition_metadata(dep_id):
    """
    Editar metadatos de una deposition → no cambia DOI.
    """
    dep = depositions.get(dep_id)
    if not dep:
        return jsonify({"error": "Deposition not found"}), 404

    payload = request.json or {}
    new_meta = payload.get("metadata", {})
    dep["metadata"].update(new_meta)
    return jsonify(dep), 200


@fakenodo_bp.route("/depositions/<dep_id>/publish", methods=["POST"])
def publish_deposition(dep_id):
    """
    Publicar una deposition → genera un record con DOI.
    """
    dep = depositions.get(dep_id)
    if not dep:
        return jsonify({"error": "Deposition not found"}), 404

    # crear record a partir de deposition
    rec_id = dep_id
    existing = records.get(rec_id)
    versions = existing["versions"] if existing else []
    new_index = len(versions)
    new_doi = versioned_doi(dep["doi_root"], new_index)

    record = {
        "id": rec_id,
        "metadata": dep["metadata"],
        "files": dep["files"],
        "doi_root": dep["doi_root"],
        "doi_current": new_doi,
        "versions": versions + [new_doi],
        "published": True,
    }
    records[rec_id] = record
    dep["published"] = True
    return jsonify(record), 200


@fakenodo_bp.route("/records/<rec_id>", methods=["GET"])
def get_record(rec_id):
    """
    Obtener un record publicado.
    """
    rec = records.get(rec_id)
    if not rec:
        return jsonify({"error": "Record not found"}), 404
    return jsonify(rec), 200


@fakenodo_bp.route("/records/<rec_id>/versions", methods=["GET"])
def list_versions(rec_id):
    """
    Listar versiones de un record.
    """
    rec = records.get(rec_id)
    if not rec:
        return jsonify({"error": "Record not found"}), 404
    return jsonify({"versions": rec["versions"], "current": rec["doi_current"]}), 200
