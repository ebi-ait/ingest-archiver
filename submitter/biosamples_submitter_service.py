from submission_broker.services.biosamples import BioSamples
from submission_broker.submission.entity import Entity

from config import BIOSTUDIES_STUDY_URL


class BioSamplesSubmitterService:

    def __init__(self, archive_client: BioSamples):
        self.__archive_client = archive_client
        self.__study_link = BIOSTUDIES_STUDY_URL

    def update_sample_with_biostudies_accession(self, entity: Entity, biostudies_accession: str):
        if biostudies_accession is None:
            return None

        entity.attributes.update(self.__create_external_references_element(biostudies_accession))

    def __create_external_references_element(self, accession):
        return {
            'externalReferences': [
                {
                    'url': self.__study_link + accession
                }
            ]
        }