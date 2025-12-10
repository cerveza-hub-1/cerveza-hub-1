import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from zipfile import ZipFile

from flask import (
    abort,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required

from app.modules.comment.services import CommentService
from app.modules.dataset import dataset_bp
from app.modules.dataset.forms import DataSetForm
from app.modules.dataset.models import DSDownloadRecord
from app.modules.dataset.services import (
    AuthorService,
    DataSetService,
    DOIMappingService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
)
from app.modules.zenodo.services import ZenodoService

from .csv_validator import validate_csv_content

logger = logging.getLogger(__name__)


dataset_service = DataSetService()
author_service = AuthorService()
dsmetadata_service = DSMetaDataService()
zenodo_service = ZenodoService()
doi_mapping_service = DOIMappingService()
ds_view_record_service = DSViewRecordService()
comment_service = CommentService()


@dataset_bp.route("/dataset/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = DataSetForm()
    if request.method == "POST":
        dataset = None

        if not form.validate_on_submit():
            return jsonify({"message": form.errors}), 400

        try:
            logger.info("Creating dataset...")
            dataset = dataset_service.create_from_form(form=form, current_user=current_user)
            logger.info(f"Created dataset: {dataset}")
            dataset_service.move_csv_models(dataset)
        except Exception as exc:
            logger.exception(f"Exception while create dataset data in local {exc}")
            return jsonify({"Exception while create dataset data in local: ": str(exc)}), 400

        # send dataset as deposition to Zenodo
        data = {}
        try:
            zenodo_response_json = zenodo_service.create_new_deposition(dataset)
            response_data = json.dumps(zenodo_response_json)
            data = json.loads(response_data)
        except Exception as exc:
            data = {}
            zenodo_response_json = {}
            logger.exception(f"Exception while create dataset data in Zenodo {exc}")

        if data.get("id"):
            deposition_id = data.get("id")

            # update dataset with deposition id in Zenodo
            dataset_service.update_dsmetadata(dataset.ds_meta_data_id, deposition_id=deposition_id)

            try:
                # iterate for each csv model (one csv model = one request to Zenodo)
                for csv_model in dataset.csv_models:
                    zenodo_service.upload_file(dataset, deposition_id, csv_model)

                # publish deposition y guardar DOI
                zenodo_response = zenodo_service.publish_deposition(deposition_id)

                doi = zenodo_response.get("doi")
                if doi:
                    dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=doi)
                    logger.info(f"DOI actualizado: {doi}")

                # update DOI
                # deposition_doi = zenodo_service.get_doi(deposition_id)
                # dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=deposition_doi)
            except Exception as e:
                msg = f"it has not been possible upload csv models in Zenodo and update the DOI: {e}"
                return jsonify({"message": msg}), 200

        # Delete temp folder
        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Everything works!"
        return jsonify({"message": msg}), 200

    return render_template("dataset/upload_dataset.html", form=form)


@dataset_bp.route("/dataset/file/validate", methods=["POST"])
@login_required
def validate_file():
    data = request.get_json()
    if not data or "content" not in data:
        return jsonify({"valid": False, "message": "No content provided"}), 400

    file_content = data["content"]

    # Usamos tu validador
    is_valid, error = validate_csv_content(file_content)
    if is_valid:
        return jsonify({"valid": True}), 200
    else:
        return jsonify({"valid": False, "error": error}), 200


@dataset_bp.route("/dataset/list", methods=["GET", "POST"])
@login_required
def list_dataset():
    return render_template(
        "dataset/list_datasets.html",
        datasets=dataset_service.get_synchronized(current_user.id),
        local_datasets=dataset_service.get_unsynchronized(current_user.id),
    )


@dataset_bp.route("/dataset/file/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("file")
    temp_folder = current_user.temp_folder()

    # Validar extensión
    if not file or not file.filename.lower().endswith(".csv"):
        return jsonify({"message": "No valid CSV file"}), 400

    # Leer contenido para validarlo
    file_content = file.read().decode("utf-8", errors="ignore")
    file.seek(0)  # IMPORTANTE

    # Validación CSV usando la nueva función
    is_valid, error = validate_csv_content(file_content)
    if not is_valid:
        return jsonify(error), 400

    # Crear carpeta temporal
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    # Generar nombre único
    file_path = os.path.join(temp_folder, file.filename)
    if os.path.exists(file_path):
        base_name, extension = os.path.splitext(file.filename)
        i = 1
        while os.path.exists(os.path.join(temp_folder, f"{base_name} ({i}){extension}")):
            i += 1
        new_filename = f"{base_name} ({i}){extension}"
        file_path = os.path.join(temp_folder, new_filename)
    else:
        new_filename = file.filename

    # Guardar archivo
    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({"message": str(e)}), 500

    return (
        jsonify(
            {
                "message": "CSV uploaded and validated successfully",
                "filename": new_filename,
            }
        ),
        200,
    )


@dataset_bp.route("/dataset/file/delete", methods=["POST"])
@login_required
def delete():
    data = request.get_json()
    filename = data.get("file")
    temp_folder = current_user.temp_folder()
    filepath = os.path.join(temp_folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": "File deleted successfully"})

    return jsonify({"error": "Error: File not found"})


@dataset_bp.route("/dataset/download/<int:dataset_id>", methods=["GET"])
def download_dataset(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)

    file_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"dataset_{dataset_id}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for subdir, dirs, files in os.walk(file_path):
            for file in files:
                full_path = os.path.join(subdir, file)
                relative_path = os.path.relpath(full_path, file_path)
                zipf.write(
                    full_path,
                    arcname=os.path.join(os.path.basename(zip_path[:-4]), relative_path),
                )

    user_cookie = request.cookies.get("download_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())
        resp = make_response(
            send_from_directory(
                temp_dir,
                f"dataset_{dataset_id}.zip",
                as_attachment=True,
                mimetype="application/zip",
            )
        )
        resp.set_cookie("download_cookie", user_cookie)
    else:
        resp = send_from_directory(
            temp_dir,
            f"dataset_{dataset_id}.zip",
            as_attachment=True,
            mimetype="application/zip",
        )

    # Check if the download record already exists for this cookie
    existing_record = DSDownloadRecord.query.filter_by(
        user_id=current_user.id if current_user.is_authenticated else None,
        dataset_id=dataset_id,
        download_cookie=user_cookie,
    ).first()

    if not existing_record:
        # Record the download in your database
        DSDownloadRecordService().create(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset_id,
            download_date=datetime.now(timezone.utc),
            download_cookie=user_cookie,
        )

    return resp


@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):
    # Check if the DOI is an old DOI
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        # Redirect to the same path with the new DOI
        return redirect(url_for("dataset.subdomain_index", doi=new_doi), code=302)

    # Try to search the dataset by the provided DOI (which should already be the new one)
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)

    if not ds_meta_data:
        abort(404)

    # Get dataset
    dataset = ds_meta_data.data_set

    # Obtener la URL del record (Fakenodo o Zenodo)
    from app.modules.zenodo.services import ZenodoService

    zenodo_service = ZenodoService()
    record_url = zenodo_service.get_record_url(dataset.ds_meta_data.deposition_id)
    is_fakenodo = zenodo_service.is_fakenodo

    user_cookie = ds_view_record_service.create_cookie(dataset=dataset)

    recs_general = dataset_service.get_similar_datasets(target_dataset_id=dataset.id, field_type="full_text_corpus")
    recs_authors = dataset_service.get_similar_datasets(target_dataset_id=dataset.id, field_type="authors")
    recs_tags = dataset_service.get_similar_datasets(target_dataset_id=dataset.id, field_type="tags")
    recs_affiliation = dataset_service.get_similar_datasets(target_dataset_id=dataset.id, field_type="affiliation")
    comments = comment_service.get_comments_for_dataset(dataset.id)

    resp = make_response(
        render_template(
            "dataset/view_dataset.html",
            dataset=dataset,
            recs_general=recs_general,
            recs_authors=recs_authors,
            recs_tags=recs_tags,
            recs_affiliation=recs_affiliation,
            comments=comments,
            record_url=record_url,
            is_fakenodo=is_fakenodo,
        )
    )
    resp.set_cookie("view_cookie", user_cookie)

    return resp


@dataset_bp.route("/dataset/unsynchronized/<int:dataset_id>/", methods=["GET"])
@login_required
def get_unsynchronized_dataset(dataset_id):
    """Muestra un dataset local (no sincronizado) del usuario actual."""

    # Get dataset
    dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)

    if not dataset:
        abort(404)

    recs_general = dataset_service.get_similar_datasets(target_dataset_id=dataset.id, field_type="full_text_corpus")
    recs_authors = dataset_service.get_similar_datasets(target_dataset_id=dataset.id, field_type="authors")
    recs_tags = dataset_service.get_similar_datasets(target_dataset_id=dataset.id, field_type="tags")
    recs_affiliation = dataset_service.get_similar_datasets(target_dataset_id=dataset.id, field_type="affiliation")

    return render_template(
        "dataset/view_dataset.html",
        dataset=dataset,
        recs_general=recs_general,
        recs_authors=recs_authors,
        recs_tags=recs_tags,
        recs_affiliation=recs_affiliation,
    )


@dataset_bp.route("/dataset/<int:dataset_id>/comments", methods=["POST"])
@login_required
def create_comment_endpoint(dataset_id):
    """Crea un comentario en un dataset."""
    data = request.get_json(silent=True)

    if data:
        content = data.get("content")
        parent_id = data.get("parent_id")
    else:
        content = request.form.get("content")
        parent_id = request.form.get("parent_id")

    if parent_id == "":
        parent_id = None

    if not content:
        return jsonify({"message": "Content is required"}), 400

    try:
        # Convertir parent_id a entero o None
        if parent_id is not None:
            parent_id = int(parent_id)

        comment = comment_service.create_comment(
            author_id=current_user.id,
            dataset_id=dataset_id,
            content=content,
            parent_id=parent_id,
        )
        return jsonify(comment.to_dict()), 201

    except Exception as e:
        logger.exception(f"Error creating comment: {e}")
        return (
            jsonify({"message": "Failed to create comment due to server error."}),
            500,
        )


@dataset_bp.route("/dataset/<int:dataset_id>/comments", methods=["GET"])
def list_comments_endpoint(dataset_id):
    """Lista los comentarios asociados a un dataset."""
    comments = comment_service.get_comments_for_dataset(dataset_id)
    comments_data = [c.to_dict() for c in comments]
    return jsonify(comments_data), 200


@dataset_bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@login_required
def delete_comment_endpoint(comment_id):
    """Permite eliminar un comentario (solo el autor del dataset)."""
    comment = comment_service.get_or_404(comment_id)
    dataset_author_id = comment.data_set.user_id

    if current_user.id != dataset_author_id:
        return (
            jsonify({"message": ("Forbidden. Only the dataset author can delete this comment.")}),
            403,
        )

    try:
        comment_service.delete_comment(comment_id)
        return jsonify({"message": "Comment deleted successfully"}), 200
    except Exception:
        return jsonify({"message": "Failed to delete comment"}), 500


@dataset_bp.route("/dataset/ranking", methods=["GET"])
def ranking():
    """Muestra la página de rankings de datasets."""
    return render_template("dataset/ranking.html")


@dataset_bp.route("/dataset/ranking/downloads", methods=["GET"])
def get_most_downloaded_datasets():
    """Obtiene el ranking de datasets más descargados (Top 5)."""
    try:
        ranking = dataset_service.get_most_downloaded_datasets(limit=5)
        return jsonify(ranking), 200
    except Exception as e:
        logger.exception(f"Error getting most downloaded datasets: {e}")
        return jsonify({"message": "Failed to get ranking"}), 500


@dataset_bp.route("/dataset/ranking/views", methods=["GET"])
def get_most_viewed_datasets():
    """Obtiene el ranking de datasets más vistos (Top 5)."""
    try:
        ranking = dataset_service.get_most_viewed_datasets(limit=5)
        return jsonify(ranking), 200
    except Exception as e:
        logger.exception(f"Error getting most viewed datasets: {e}")
        return jsonify({"message": "Failed to get ranking"}), 500
