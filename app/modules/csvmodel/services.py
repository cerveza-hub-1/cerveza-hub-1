from app.modules.csvmodel.repositories import CSVModelRepository, FMMetaDataRepository
from app.modules.hubfile.services import HubfileService
from core.services.BaseService import BaseService


class CSVModelService(BaseService):
    def __init__(self):
        super().__init__(CSVModelRepository())
        self.hubfile_service = HubfileService()

    def total_csv_model_views(self) -> int:
        return self.hubfile_service.total_hubfile_views()

    def total_csv_model_downloads(self) -> int:
        return self.hubfile_service.total_hubfile_downloads()

    def count_csv_models(self):
        return self.repository.count_csv_models()

    class FMMetaDataService(BaseService):
        def __init__(self):
            super().__init__(FMMetaDataRepository())
