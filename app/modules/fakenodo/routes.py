from flask import jsonify, render_template, request, url_for

from app.modules.dataset.models import DSMetaData
from app.modules.fakenodo import fakenodo_bp
from app.modules.fakenodo.services import FakenodoService

service = FakenodoService()


@fakenodo_bp.route("/", methods=["GET"])
def index():
    # Página simple de bienvenida
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
    try:
        record = service.repository.get_or_404(int(record_id))

        files = []

        # Determinar qué archivos se están subiendo
        if "file" in request.files:
            uploaded = request.files["file"]
            filename = request.form.get("name", uploaded.filename)
            files = [filename]
        elif request.is_json:
            data = request.get_json() or {}
            files = data.get("files", [])

        # Guardar los archivos en la última versión del registro
        if record.versions:
            latest_version = record.versions[-1]
            if "files" not in latest_version:
                latest_version["files"] = []

            # Agregar nuevos archivos (evitar duplicados)
            for file in files:
                if file not in latest_version["files"]:
                    latest_version["files"].append(file)

        return jsonify(
            {
                "record_id": record_id,
                "message": f"Files uploaded: {files}",
                "files": files,
            }
        ), 201

    except KeyError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@fakenodo_bp.route("/api/records", methods=["GET"])
def list_records():
    return jsonify({"records": service.list_all()}), 200


@fakenodo_bp.route("/records/<record_id>", methods=["GET"])
def view_record_page(record_id):
    try:
        record = service.get_record(record_id)

        print(f"=== DEBUG Fakenodo Record {record_id} ===")
        print(f"Record DOI: {record.get('doi')}")
        print(f"Record metadata: {record.get('metadata', {})}")

        # INICIALIZAR
        dataset = None
        deposition_id = None

        # SOLO ESTRATEGIA: Buscar por DOI del registro
        if record.get("doi"):
            doi = record["doi"]
            print(f"Searching for dataset with DOI: {doi}")

            # Buscar en DSMetaData por dataset_doi
            ds_meta_data = DSMetaData.query.filter_by(dataset_doi=doi).first()

            if ds_meta_data:
                print(f"Found dataset by DOI: {doi}")
                print(f"Dataset ID: {ds_meta_data.data_set.id}")
                print(f"Dataset title: {ds_meta_data.title}")
                dataset = ds_meta_data.data_set
            else:
                print(f"No dataset found with DOI: {doi}")

                # DEBUG: Mostrar todos los DOIs en el sistema
                all_ds_meta = DSMetaData.query.all()
                print("All DOIs in CSVHub:")
                for ds in all_ds_meta:
                    if ds.dataset_doi:
                        print(f"  - {ds.dataset_doi} (Dataset ID: {ds.data_set.id})")
        else:
            print("Record has no DOI, cannot search for dataset")

        # Obtener archivos del dataset (SOLO si se encontró por DOI)
        files = []
        if dataset:
            print(f"Processing files for dataset ID: {dataset.id}")
            for csv_model in dataset.csv_models:
                for file in csv_model.files:
                    files.append(
                        {
                            "name": file.name,
                            "size": file.get_formatted_size(),
                            "url": url_for(
                                "hubfile.download_file", file_id=file.id, _external=True
                            ),
                            "source": "csvhub",
                        }
                    )
            print(f"Found {len(files)} files in dataset")

        # Archivos de Fakenodo (si los hay)
        fakenodo_files = []
        if record.get("files"):
            for filename in record["files"]:
                fakenodo_files.append(
                    {"name": filename, "size": "Unknown", "source": "fakenodo"}
                )

        # NO generar placeholders - si no hay archivos, mostrar vacío
        # (eliminamos la generación automática)

        return render_template(
            "record_view.html",
            record=record,
            record_url=request.url,
            files=files,  # Solo archivos encontrados por DOI
            fakenodo_files=fakenodo_files,
            dataset=dataset,
            found_dataset=dataset is not None,
            deposition_id=deposition_id,
            search_method="doi-only",  # Cambiado para reflejar la nueva estrategia
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        return render_template(
            "record_view.html",
            record={"error": str(e), "id": record_id},
            record_url=request.url,
            files=[],
            fakenodo_files=[],
            dataset=None,
            found_dataset=False,
        )
