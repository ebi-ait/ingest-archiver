from abc import abstractmethod, ABCMeta
from datetime import datetime
from typing import Tuple, List


from submission_broker.submission.submission import Entity
from converter.biosamples import BioSamplesConverter
from converter.biostudies import BioStudiesConverter
from converter.ena.ena_study import EnaStudyConverter
from converter.ena.ena_sample import EnaSampleConverter

from archiver import first_element_or_self, ArchiveResponse, ConvertedEntity
from hca.submission import HcaSubmission

CREATED_ENTITY = 'CREATED'
UPDATED_ENTITY = 'UPDATED'
ERRORED_ENTITY = 'ERRORED'

ARCHIVE_TO_HCA_ENTITY_MAP = {
    'BioSamples': ['biomaterials'],
    'BioStudies': ['projects'],
    'ENA': ['projects', 'biomaterials']
}

CONVERTERS_BY_ARCHIVE_TYPES = {
    'BioSamples_biomaterials': BioSamplesConverter(),
    'BioStudies_projects': BioStudiesConverter(),
    'ENA_projects': EnaStudyConverter(),
    'ENA_biomaterials': EnaSampleConverter()
}


class Submitter(metaclass=ABCMeta):
    def __init__(self, archive_client, converter, updater):
        self.archive_client = archive_client
        self.converter = converter
        self.release_date = None
        self.updater = updater

    def convert_all_entities(self, submission: HcaSubmission, archive_type: str, additional_attributes: dict = None)\
            -> List[ConvertedEntity]:
        if additional_attributes is None:
            additional_attributes = {}
        hca_entity_types = ARCHIVE_TO_HCA_ENTITY_MAP[archive_type]
        converted_entities = []
        for hca_entity_type in hca_entity_types:
            if archive_type == 'ENA':
                self.__setup_converter_for_ena(archive_type, hca_entity_type)
            converted_entities.extend(self.__convert_entities_by_hca_type(additional_attributes, archive_type,
                                                                     hca_entity_type, submission))
            if archive_type == 'ENA':
                xml_entity_str = self.converter.convert_entity_to_xml_str()
                if xml_entity_str:
                    converted_entities.append(
                        ConvertedEntity(data=xml_entity_str,
                                        is_update=self.converter.is_update,
                                        hca_entity_type=hca_entity_type))
        return converted_entities

    def __convert_entities_by_hca_type(self, additional_attributes, archive_type, hca_entity_type,
                                       submission):
        converted_entities = []
        for entity in submission.get_entities(hca_entity_type):
            is_update = False
            self.__add_uuid_to_additional_attributes(additional_attributes, entity)
            if archive_type == 'ENA':
                self.__set_release_date_from_project(entity)
            accession = self.__get_accession(entity, archive_type)
            if accession:
                is_update = True
            converted_entity = self.__convert_entity(entity, accession, additional_attributes)
            if archive_type != 'ENA':
                converted_entities.append(
                    ConvertedEntity(data=converted_entity, is_update=is_update, hca_entity_type=hca_entity_type))
            self.__cleanup_additional_attributes(additional_attributes)
        return converted_entities

    def __setup_converter_for_ena(self, archive_type, hca_entity_type):
        self.converter = CONVERTERS_BY_ARCHIVE_TYPES[f'{archive_type}_{hca_entity_type}']
        self.converter.init_ena_set()

    @staticmethod
    def __add_uuid_to_additional_attributes(additional_attributes, entity):
        uuid = entity.attributes.get('uuid', {}).get('uuid', '')
        additional_attributes['alias'] = uuid

    @staticmethod
    def __cleanup_additional_attributes(additional_attributes):
        additional_attributes.pop('accession', None)
        additional_attributes.pop('alias', None)

    def send_all_entities(self, converted_entities, archive_type: str):
        responses_from_archive = []
        if archive_type == 'ENA':
            responses_from_archive = self._submit_to_archive(converted_entities)
        else:
            for converted_entity in converted_entities:
                archive_response: dict = self._submit_to_archive(converted_entity)
                responses_from_archive.append(archive_response)

        return responses_from_archive

    def process_responses(self, submission: HcaSubmission, responses, error_key, archive_type):
        responses_from_archive = {}
        response: ArchiveResponse
        for response in responses:
            result, archive_response = self.__process_response(response)
            accession = response.data.get('accession')
            if accession:
                entity_type = response.entity_type
                uuid = response.data.get('uuid')
                entity = submission.get_entity_by_uuid(entity_type, uuid)
                entity.add_accession(archive_type, accession)
                submission.add_accessions_to_attributes(entity)
                self.updater.update_entity(entity)

            responses_from_archive.setdefault(result, []).append(archive_response)
        return responses_from_archive

    def __set_release_date_from_project(self, entity):
        if entity.identifier.entity_type == 'projects':
            release_date = entity.attributes.get('releaseDate')
            if release_date:
                self.release_date = datetime.strptime(release_date, "%Y-%m-%dT%H:%M:%SZ").date().strftime('%d-%m-%Y')

    def __convert_entity(self, entity: Entity, accession: str = None, other_attributes: dict = None) -> dict:
        if other_attributes is None:
            other_attributes = {}

        if accession is not None:
            other_attributes['accession'] = accession
        converted_entity = self.converter.convert(entity.attributes, other_attributes)
        return converted_entity

    def __process_response(self, response: ArchiveResponse) -> Tuple[str, ArchiveResponse]:
        archive_response = response.data
        if 'error_messages' in archive_response:
            return ERRORED_ENTITY, response
        else:
            if response.is_update:
                return UPDATED_ENTITY, response
            else:
                return CREATED_ENTITY, response

    @staticmethod
    def __get_accession(entity, entity_type):
        accession = first_element_or_self(entity.get_accession(entity_type))
        # TODO We have to do it because of our inconsistant schema.
        # This should be moved to submission_broker when we set the accession
        if isinstance(accession, list):
            accession = accession[0]
        return accession

    @abstractmethod
    def _submit_to_archive(self, converted_entity):
        raise NotImplementedError
