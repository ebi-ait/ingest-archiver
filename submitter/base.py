from abc import abstractmethod, ABCMeta

from submission_broker.submission.submission import Submission, Entity

CREATED_ENTITY = 'CREATED'
UPDATED_ENTITY = 'UPDATED'
ERRORED_ENTITY = 'ERRORED'

ARCHIVE_TO_HCA_ENTITY_MAP = {
    'BioSamples': 'biomaterials',
    'BioStudies': 'projects'
}


class Submitter(metaclass=ABCMeta):
    def __init__(self, archive_client, converter):
        self.archive_client = archive_client
        self.converter = converter

    def send_all_entities(self, submission: Submission, archive_type: str, error_key: str,
                          additional_attributes: dict = None) -> dict:
        response = {}
        hca_entity_type = ARCHIVE_TO_HCA_ENTITY_MAP[archive_type]
        for entity in submission.get_entities(hca_entity_type):
            result = self.send_entity(entity, archive_type, error_key, additional_attributes)
            response.setdefault(result, []).append(entity)
        return response

    def send_entity(self, entity: Entity, entity_type: str, error_key: str,
                    other_attributes: dict = {}) -> str:
        accession = entity.get_accession(entity_type.capitalize())
        if accession is not None:
            other_attributes['accession'] = accession
        converted_entity = self.converter.convert(entity.attributes, other_attributes)
        try:
            response = self._submit_to_archive(converted_entity)
            if 'accession' in response and not accession:
                entity.add_accession(entity_type, response['accession'])
                return CREATED_ENTITY
            return UPDATED_ENTITY
        except Exception as e:
            error_msg = f'{entity_type} Error: {e}'
            entity.add_error(error_key, error_msg)
            return ERRORED_ENTITY

    @abstractmethod
    def _submit_to_archive(self, converted_entity):
        raise NotImplementedError
