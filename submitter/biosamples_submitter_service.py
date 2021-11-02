from submission_broker.services.biosamples import BioSamples
from submission_broker.submission.entity import Entity

BIOSTUDIES_STUDY_LINK = 'https://www{}.ebi.ac.uk/biostudies/studies/'


class BioSamplesSubmitterService:

    def __init__(self, archive_client: BioSamples, deployment_env: str):
        self.__archive_client = archive_client
        self.__deployment_env = 'dev' if deployment_env.lower() in ('dev', 'staging') else ''

    def update_sample_with_biostudies_accession(self, entity: Entity, biostudies_accession: str):
        if biostudies_accession is None:
            return None

        entity.attributes.update(self.__create_external_references_element(biostudies_accession))

    def __create_external_references_element(self, accession):
        return {
            'externalReferences': [
                {
                    'url': BIOSTUDIES_STUDY_LINK.format(self.__deployment_env) + accession
                }
            ]
        }