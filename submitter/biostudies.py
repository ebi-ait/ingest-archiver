from submission_broker.services.biostudies import BioStudies
from submission_broker.submission.submission import Submission, Entity

from converter.biostudies import BioStudiesConverter
from submitter.base import Submitter

ERROR_KEY = 'content.project_core.biostudies_accession'


class BioStudiesSubmitter(Submitter):
    def __init__(self, archive_client: BioStudies, converter: BioStudiesConverter):
        super().__init__(archive_client, converter)
        self.__archive_client = archive_client
        self.__converter = converter

    def send_all_projects(self, submission: Submission) -> dict:
        response = self.send_all_entities(submission, "BioStudies", ERROR_KEY)

        return response

    def _submit_to_archive(self, converted_entity):
        response = {'accession': self.__archive_client.send_submission(converted_entity)}

        return response
