from submission_broker.services.biosamples import BioSamples
from submission_broker.submission.entity import Entity

ENV = 'dev'
BIOSTUDIES_STUDY_LINK = f"https://www{ENV}.ebi.ac.uk/biostudies/studies/"


class BioSamplesSubmitterService:

    def __init__(self, archive_client: BioSamples):
        self.__archive_client = archive_client

    def update_sample_with_biostudies_accession(self, entity: Entity, biostudies_accession: str):
        if biostudies_accession is None:
            return None

        entity.attributes.update(self.__create_external_references_element(biostudies_accession))

    @staticmethod
    def __create_external_references_element(accession):
        return {
            'externalReferences': [
                {
                    'url': BIOSTUDIES_STUDY_LINK + accession
                }
            ]
        }