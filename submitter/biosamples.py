from typing import Tuple, List

from converter.biosamples import BioSamplesConverter
from submission_broker.submission.submission import Submission, Entity
from submission_broker.services.biosamples import BioSamples, AapClient

from submitter.base import Submitter
from submitter.biosamples_submitter_service import BioSamplesSubmitterService

ERROR_KEY = 'content.biomaterial_core.biosamples_accession'


class BioSamplesSubmitter(Submitter):
    def __init__(self, archive_client: BioSamples, converter: BioSamplesConverter,
                 submitter_service: BioSamplesSubmitterService):
        super().__init__(archive_client, converter)
        self.__archive_client = archive_client
        self.__converter = converter
        self.__submitter_service = submitter_service

    def send_all_samples(self, submission: Submission) -> Tuple[dict, List[str]]:
        additional_attributes = self.__create_additional_attributes(submission)
        response, accessions = self.send_all_entities(submission, "BioSamples", ERROR_KEY, additional_attributes)

        return response, accessions

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
