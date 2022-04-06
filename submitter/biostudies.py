from submission_broker.services.biostudies import BioStudies
from typing import List

from archiver import ArchiveResponse, ConvertedEntity
from converter.biostudies import BioStudiesConverter
from hca.submission import HcaSubmission
from hca.updater import HcaUpdater
from submitter.base import Submitter
from submitter.biostudies_submitter_service import BioStudiesSubmitterService

ARCHIVE_TYPE = "BioStudies"

ERROR_KEY = 'content.project_core.biostudies_accession'


class BioStudiesSubmitter(Submitter):
    def __init__(self, archive_client: BioStudies, converter: BioStudiesConverter,
                 submitter_service: BioStudiesSubmitterService, updater: HcaUpdater):
        super().__init__(archive_client, converter, updater)
        self.__archive_client = archive_client
        self.__converter = converter
        self.__submitter_service = submitter_service

    def send_all_projects(self, submission: HcaSubmission) -> dict:
        converted_entities = self.convert_all_entities(submission, ARCHIVE_TYPE)
        responses = self.send_all_entities(converted_entities, ARCHIVE_TYPE)
        self.process_responses(submission, responses, ERROR_KEY, ARCHIVE_TYPE)

        project_response = responses[0]
        project_response['info'] = 'BioStudies from HCA projects'

        return project_response

    def update_submission_with_archive_accessions(self, biosample_accessions: List[str], biostudies_accession,
                                                  ena_accessions: List[str]):
        if not BioStudiesSubmitter.__has_accessions(biosample_accessions, ena_accessions):
            return

        biostudies_submission = self.__submitter_service.get_biostudies_payload_by_accession(biostudies_accession).json

        self.__update_submission_with_biosamples_accessions(biosample_accessions, biostudies_submission)
        self.__update_submission_with_ena_accessions(ena_accessions, biostudies_submission)
        self.__archive_client.send_submission(biostudies_submission)

    def __update_submission_with_biosamples_accessions(self, biosample_accessions, biostudies_submission):
        self.__submitter_service.update_submission_with_accessions_by_type(
            biostudies_submission, biosample_accessions, BioStudiesSubmitterService.BIOSAMPLE_LINK_TYPE)

    def __update_submission_with_ena_accessions(self, ena_accessions, biostudies_submission):
        self.__submitter_service.update_submission_with_accessions_by_type(
            biostudies_submission, ena_accessions, BioStudiesSubmitterService.ENA_LINK_TYPE)

    @staticmethod
    def __has_accessions(biosample_accessions, ena_accessions) -> bool:
        if BioStudiesSubmitter.__has_accession(biosample_accessions)\
                or BioStudiesSubmitter.__has_accession(ena_accessions):
            return True
        return False

    @staticmethod
    def __has_accession(accessions) -> bool:
        return accessions is not None and len(accessions) > 0

    def _submit_to_archive(self, converted_entity: ConvertedEntity):
        accession = self.__archive_client.send_submission(converted_entity.data)

        for attribute in converted_entity.data.get('attributes', []):
            if attribute and attribute.get('name') == 'HCA Project UUID':
                uuid = attribute.get('value')
                break

        response = {
            "entity_type": converted_entity.hca_entity_type,
            "uuid": uuid,
            "biostudies_accession": accession,
            "is_update": converted_entity.updated
        }

        return response
