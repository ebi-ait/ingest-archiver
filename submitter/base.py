from abc import abstractmethod, ABCMeta
from datetime import datetime
from typing import Tuple, List

from submission_broker.submission.submission import Entity

from archiver import first_element_or_self, ArchiveResponse
from hca.submission import HcaSubmission

CREATED_ENTITY = 'CREATED'
UPDATED_ENTITY = 'UPDATED'
ERRORED_ENTITY = 'ERRORED'

ARCHIVE_TO_HCA_ENTITY_MAP = {
    'BioSamples': 'biomaterials',
    'BioStudies': 'projects',
    'ENA': 'projects'
}


class Submitter(metaclass=ABCMeta):
    def __init__(self, archive_client, converter, updater):
        self.archive_client = archive_client
        self.converter = converter
        self.release_date = None
        self.updater = updater

    def send_all_entities(self, submission: HcaSubmission, archive_type: str, error_key: str,
                          additional_attributes: dict = None) -> dict:
        if additional_attributes is None:
            additional_attributes = {}
        response = {}
        hca_entity_type = ARCHIVE_TO_HCA_ENTITY_MAP[archive_type]
        for entity in submission.get_entities(hca_entity_type):
            if archive_type == 'ENA' and hca_entity_type == 'projects':
                self.__set_release_date_from_project(entity)
            result, archive_response = self.send_entity(entity, archive_type, error_key, additional_attributes)

            submission.add_accessions_to_attributes(entity)
            # self.updater.update_entity(entity)

            response.setdefault(result, []).append(archive_response)
            additional_attributes.pop('accession', None)
        return response

    def __set_release_date_from_project(self, entity):
        release_date = entity.attributes.get('releaseDate')
        if release_date:
            self.release_date = datetime.strptime(release_date, "%Y-%m-%dT%H:%M:%SZ").date().strftime('%d-%m-%Y')

    def send_entity(self, entity: Entity, entity_type: str, error_key: str,
                    other_attributes: dict = None) -> Tuple[str, str]:
        accession = self.__get_accession(entity, entity_type)

        if other_attributes is None:
            other_attributes = {}

        if accession is not None:
            other_attributes['accession'] = accession
        converted_entity = self.__convert_entity(entity, other_attributes)
        try:
            response = self._submit_to_archive(converted_entity)
            if 'accession' in response and not accession:
                accession = response.get('accession')
                entity.add_accession(entity_type, accession)
                return CREATED_ENTITY, ArchiveResponse(entity.identifier.entity_type, accession)
            elif 'error_messages' in response:
                error_messages = response.get('error_messages')
                entity.add_error(error_key, error_messages)
                return ERRORED_ENTITY, ArchiveResponse(entity.identifier.entity_type, accession, error_messages)
            return UPDATED_ENTITY, ArchiveResponse(entity.identifier.entity_type, accession)
        except Exception as e:
            error_msg = f'{entity_type} Error: {e}'
            entity.add_error(error_key, error_msg)
            return ERRORED_ENTITY, ArchiveResponse(entity.identifier.entity_type, accession, error_messages)

    def __get_accession(self, entity, entity_type):
        accession = first_element_or_self(entity.get_accession(entity_type))
        # TODO We have to do it because of our inconsistant schema.
        # This should be moved to submission_broker when we set the accession
        if isinstance(accession, list):
            accession = accession[0]
        return accession

    def __convert_entity(self, entity, other_attributes):
        return self.converter.convert(entity.attributes, other_attributes)

    @abstractmethod
    def _submit_to_archive(self, converted_entity):
        raise NotImplementedError
