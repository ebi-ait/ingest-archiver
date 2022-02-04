from submission_broker.services.biostudies import BioStudies

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
        processed_responses = self.process_responses(submission, responses, ERROR_KEY, ARCHIVE_TYPE)

        return processed_responses

    def update_submission_with_sample_accessions(self, biosample_accessions: list, biostudies_accession):
        biostudies_submission = \
            self.__submitter_service.update_submission_with_sample_accessions(biosample_accessions, biostudies_accession)
        self.__archive_client.send_submission(biostudies_submission)

        return biostudies_submission

    def _submit_to_archive(self, converted_entity: ConvertedEntity):
        data = {'accession': self.__archive_client.send_submission(converted_entity.data)}

        for attribute in converted_entity.data.get('attributes', []):
            if attribute and attribute.get('name') == 'HCA Project UUID':
                data['uuid'] = attribute.get('value', '')
                break

        response = \
            ArchiveResponse(
                entity_type=converted_entity.hca_entity_type, data=data, is_update=converted_entity.is_update)

        return response
