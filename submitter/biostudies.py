from submission_broker.services.biostudies import BioStudies

from converter.biostudies import BioStudiesConverter
from hca.submission import HcaSubmission
from hca.updater import HcaUpdater
from submitter.base import Submitter
from submitter.biostudies_submitter_service import BioStudiesSubmitterService

ERROR_KEY = 'content.project_core.biostudies_accession'


class BioStudiesSubmitter(Submitter):
    def __init__(self, archive_client: BioStudies, converter: BioStudiesConverter,
                 submitter_service: BioStudiesSubmitterService, updater: HcaUpdater):
        super().__init__(archive_client, converter, updater)
        self.__archive_client = archive_client
        self.__converter = converter
        self.__submitter_service = submitter_service

    def send_all_projects(self, submission: HcaSubmission) -> dict:
        biostudies_responses = self.send_all_entities(submission, "BioStudies", ERROR_KEY)

        return biostudies_responses

    def update_submission_with_sample_accessions(self, biosample_accessions: list, biostudies_accession):
        biostudies_submission = \
            self.__submitter_service.update_submission_with_sample_accessions(biosample_accessions, biostudies_accession)
        self.__archive_client.send_submission(biostudies_submission)

        return biostudies_submission

    def _submit_to_archive(self, converted_entity):
        response = {'accession': self.__archive_client.send_submission(converted_entity)}

        return response
