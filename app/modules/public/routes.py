import logging

from flask import render_template

from app.modules.csvmodel.services import CSVModelService
from app.modules.dataset.services import DataSetService
from app.modules.public import public_bp

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    logger.info("Access index")
    dataset_service = DataSetService()
    csv_model_service = CSVModelService()

    # Statistics: total datasets and csv models
    datasets_counter = dataset_service.count_synchronized_datasets()
    csv_models_counter = csv_model_service.count_csv_models()

    # Statistics: total downloads
    total_dataset_downloads = dataset_service.total_dataset_downloads()
    total_csv_model_downloads = csv_model_service.total_csv_model_downloads()

    # Statistics: total views
    total_dataset_views = dataset_service.total_dataset_views()
    total_csv_model_views = csv_model_service.total_csv_model_views()

    return render_template(
        "public/index.html",
        datasets=dataset_service.latest_synchronized(),
        datasets_counter=datasets_counter,
        csv_models_counter=csv_models_counter,
        total_dataset_downloads=total_dataset_downloads,
        total_csv_model_downloads=total_csv_model_downloads,
        total_dataset_views=total_dataset_views,
        total_csv_model_views=total_csv_model_views,
    )
