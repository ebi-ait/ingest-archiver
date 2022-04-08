import logging

from requests import HTTPError

from archiver import ConvertedEntity
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

    def send_all_samples(self, submission: HcaSubmission, update_only: bool = False) -> dict:
        additional_attributes = self.__create_additional_attributes(submission)
        converted_entities = self.convert_all_entities(submission, ARCHIVE_TYPE, additional_attributes)
        responses = self.send_all_entities(converted_entities, ARCHIVE_TYPE)

        if update_only:
            return {}

        self.process_responses(submission, responses, ERROR_KEY, ARCHIVE_TYPE)

        return {
            'info': 'Biosamples from HCA biomaterials',
            'entities': responses
        }

    def update_samples_with_biostudies_accession(self, submission, biosample_accessions, biostudies_accession):
        for entity in submission.get_entities('biomaterials'):
            self.__submitter_service.update_sample_with_biostudies_accession(
                entity, biostudies_accession)
        self.send_all_samples(submission, update_only=True)

    def _submit_to_archive(self, converted_entity: ConvertedEntity):
        response = {
            "entity_type": converted_entity.hca_entity_type,
            "is_update": converted_entity.updated
        }

        try:
            rest_error_message = None
            data = self.__archive_client.send_sample(converted_entity.data)
            response['biosamples_accession'] = data.get("accession")
        except HTTPError as rest_error:
            logging.error('BioSamples service returned with an error.')
            logging.error(f'Http return code: {rest_error.response.status_code}')
            logging.error(f'Error message: {rest_error.response.text}')
            rest_error_message = rest_error.response.text

        for attribute in converted_entity.data.attributes:
            if attribute and attribute.name == 'HCA Biomaterial UUID':
                response['uuid'] = attribute.value
                break

        if rest_error_message:
            response['error'] = rest_error_message

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
