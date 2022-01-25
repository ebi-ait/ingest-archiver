from converter.biosamples import BioSamplesConverter
from submission_broker.submission.submission import Submission
from submission_broker.services.biosamples import BioSamples

from hca.submission import HcaSubmission
from hca.updater import HcaUpdater
from submitter.base import Submitter
from submitter.biosamples_submitter_service import BioSamplesSubmitterService

ARCHIVE_TYPE = "BioSamples"

ERROR_KEY = 'content.biomaterial_core.biosamples_accession'


class BioSamplesSubmitter(Submitter):
    def __init__(self, archive_client: BioSamples, converter: BioSamplesConverter,
                 submitter_service: BioSamplesSubmitterService, updater: HcaUpdater):
        super().__init__(archive_client, converter, updater)
        self.__archive_client = archive_client
        self.__converter = converter
        self.__submitter_service = submitter_service

    def send_all_samples(self, submission: HcaSubmission) -> dict:
        additional_attributes = self.__create_additional_attributes(submission)
        converted_entities = self.convert_all_entities(submission, ARCHIVE_TYPE, additional_attributes)
        responses = self.send_all_entities(converted_entities, ARCHIVE_TYPE)
        processed_responses = self.process_responses(submission, responses, ERROR_KEY)

        return processed_responses

    def update_samples_with_biostudies_accession(self, submission, biosample_accessions, biostudies_accession):
        for entity in submission.get_entities('biomaterials'):
            self.__submitter_service.update_sample_with_biostudies_accession(
                entity, biostudies_accession)
            self.send_entity(entity, "BioSamples", ERROR_KEY, {})

    def _submit_to_archive(self, converted_entity):
        response = self.__archive_client.send_sample(converted_entity)

        return response

    def __create_additional_attributes(self, submission):
        project_release_date = self.__get_project_release_date_from_submission(submission)
        other_attributes = {'release_date': project_release_date}
        return other_attributes

    @staticmethod
    def __get_project_release_date_from_submission(submission: Submission) -> str:
        projects = submission.get_entities('projects')
        for project in projects:
            if 'releaseDate' in project.attributes:
                return project.attributes['releaseDate']
