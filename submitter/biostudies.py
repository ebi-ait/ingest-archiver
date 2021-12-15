from typing import List, Tuple

from submission_broker.services.biostudies import BioStudies
from submission_broker.submission.submission import Submission

from converter.biostudies import BioStudiesConverter
from submitter.base import Submitter
from submitter.biostudies_submitter_service import BioStudiesSubmitterService

ERROR_KEY = 'content.project_core.biostudies_accession'


class BioStudiesSubmitter(Submitter):
    def __init__(self, archive_client: BioStudies, converter: BioStudiesConverter,
                 submitter_service: BioStudiesSubmitterService):
        super().__init__(archive_client, converter)
        self.__archive_client = archive_client
        self.__converter = converter
        self.__submitter_service = submitter_service

    def send_all_projects(self, submission: Submission) -> Tuple[dict, List[str]]:
        response, accessions = self.send_all_entities(submission, "BioStudies", ERROR_KEY)

        return response, accessions

    def update_submission_with_sample_accessions(self, biosample_accessions: list, biostudies_accession):
        biostudies_submission = \
            self.__submitter_service.update_submission_with_sample_accessions(biosample_accessions, biostudies_accession)
        self.__archive_client.send_submission(biostudies_submission)

        return biostudies_submission

    def _submit_to_archive(self, converted_entity):
        response = {'accession': self.__archive_client.send_submission(converted_entity)}

        return response
