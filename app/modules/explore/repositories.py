import re

import unidecode
from sqlalchemy import any_, or_

from app.modules.dataset.models import Author, DataSet, DSMetaData, PublicationType
from app.modules.featuremodel.models import FeatureModel, FMMetaData
from core.repositories.BaseRepository import BaseRepository


class ExploreRepository(BaseRepository):
    def __init__(self):
        super().__init__(DataSet)

    def filter(
        self,
        query="",
        sorting="newest",
        publication_type="any",
        tags=None,
        description="",
        authors="",
        affiliation="",
        orcid="",
        csv_filename="",
        csv_title="",
        publication_doi="",
        **kwargs,
    ):

        datasets = (
            self.model.query.join(DataSet.ds_meta_data)
            .join(DSMetaData.authors)
            .join(DataSet.feature_models)
            .join(FeatureModel.fm_meta_data)
        )

        normalized_query = unidecode.unidecode(query).lower()
        cleaned_query = re.sub(r'[,.":\'()\[\]^;!¡¿?]', "", normalized_query)
        datasets = datasets.filter(DSMetaData.dataset_doi.isnot(None))
        if query:
            datasets = datasets.filter(DSMetaData.title.ilike(f"%{cleaned_query}%"))

        if description:
            datasets = datasets.filter(DSMetaData.description.ilike(f"%{description}%"))
        if authors:
            datasets = datasets.filter(Author.name.ilike(f"%{authors}%"))
        if affiliation:
            datasets = datasets.filter(Author.affiliation.ilike(f"%{affiliation}%"))
        if orcid:
            datasets = datasets.filter(Author.orcid.ilike(f"%{orcid}%"))
        if csv_filename:
            datasets = datasets.filter(FMMetaData.uvl_filename.ilike(f"%{csv_filename}%"))
        if csv_title:
            datasets = datasets.filter(FMMetaData.title.ilike(f"%{csv_title}%"))
        if publication_doi:
            datasets = datasets.filter(FMMetaData.publication_doi.ilike(f"%{publication_doi}%"))
        if tags:
            datasets = datasets.filter(or_(FMMetaData.tags.ilike(f"%{tags}%"), DSMetaData.tags.ilike(f"%{tags}%")))

        if publication_type != "any":
            for member in PublicationType:
                if member.value.lower() == publication_type:
                    datasets = datasets.filter(DSMetaData.publication_type == member.name)
                    break

        # Orden
        datasets = datasets.order_by(
            self.model.created_at.asc() if sorting == "oldest" else self.model.created_at.desc()
        )

        return datasets.all()
