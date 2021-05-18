from converter.biosamples import BioSamplesConverter
from submission_broker.submission.submission import Submission, Entity
from submission_broker.services.biosamples import BioSamples, AapClient

from submitter.base import Submitter

ERROR_KEY = 'content.biomaterial_core.biosamples_accession'


class BioSamplesSubmitter(Submitter):
    def __init__(self, archive_client: BioSamples, converter: BioSamplesConverter):
        super().__init__(archive_client, converter)
        self.__archive_client = archive_client
        self.__converter = converter

    def send_all_samples(self, submission: Submission) -> dict:
        project_release_date = self.__get_project_release_date_from_submission(submission)
        other_attributes = {'release_date': project_release_date}
        response = self.send_all_entities(submission, "BioSamples", ERROR_KEY, other_attributes)

        return response

    def _submit_to_archive(self, converted_entity):
        response = self.__archive_client.send_sample(converted_entity)

        return response

    @staticmethod
    def __get_project_release_date_from_submission(submission: Submission) -> str:
        projects = submission.get_entities('projects')
        for project in projects:
            if 'releaseDate' in project.attributes:
                return project.attributes['releaseDate']
