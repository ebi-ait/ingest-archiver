from abc import abstractmethod, ABCMeta
from datetime import datetime
from typing import Tuple, List, Union

from lxml import etree

from submission_broker.submission.submission import Entity, Submission
from converter.biosamples import BioSamplesConverter
from converter.biostudies import BioStudiesConverter
from converter.ena.ena_study import EnaStudyConverter
from converter.ena.ena_sample import EnaSampleConverter
from converter.ena.base import BaseEnaConverter

from archiver import first_element_or_self, ArchiveResponse
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
            -> List[Union[Tuple[dict, bool, str], Tuple[str, bool, str]]]:
        if additional_attributes is None:
            additional_attributes = {}
        hca_entity_types = ARCHIVE_TO_HCA_ENTITY_MAP[archive_type]
        converted_entities = []
        for hca_entity_type in hca_entity_types:
            is_update = False
            if archive_type == 'ENA':
                self.converter = CONVERTERS_BY_ARCHIVE_TYPES[f'{archive_type}_{hca_entity_type}']
            for entity in submission.get_entities(hca_entity_type):
                uuid = entity.attributes.get('uuid', {}).get('uuid', '')
                additional_attributes['alias'] = uuid
                if archive_type == 'ENA' and hca_entity_type == 'projects':
                    self.__set_release_date_from_project(entity)
                accession = self.__get_accession(entity, archive_type)
                if accession:
                    is_update = True
                converted_entity = self.__convert_entity(entity, accession, additional_attributes)
                additional_attributes.pop('accession', None)
                additional_attributes.pop('alias', None)
                if archive_type != 'ENA':
                    converted_entities.append((converted_entity, is_update, hca_entity_type))
                    is_update = False
            if archive_type == 'ENA':
                ena_converter: BaseEnaConverter = self.converter
                converted_ena_entity = ena_converter.ena_set
                etree.indent(converted_ena_entity, space="    ")
                converted_ena_xml = ena_converter.convert_to_xml_str(converted_ena_entity)
                converted_entities.append((converted_ena_xml, is_update, hca_entity_type))
        return converted_entities

    def send_all_entities(self, converted_entities, archive_type: str):
        responses_from_archive = []
        if archive_type == 'ENA':
            responses_from_archive = self._submit_to_archive(converted_entities)
        else:
            for converted_entity, is_update, entity_type in converted_entities:
                archive_response = self._submit_to_archive(converted_entity)
                responses_from_archive.append((archive_response, is_update, entity_type))

        return responses_from_archive

    def process_responses(self, submission: Submission, responses, error_key):
        responses_from_archive = {}
        for response in responses:
            result, archive_response = self.__process_response(submission, response, error_key)
            # submission.add_accessions_to_attributes(entity)
            # self.updater.update_entity(entity)

            responses_from_archive.setdefault(result, []).append(archive_response)
        return responses_from_archive

    def __set_release_date_from_project(self, entity):
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

    def __process_response(self, submission: Submission, response, error_key: str) \
            -> Tuple[str, ArchiveResponse]:
        archive_response = response[0]
        entity_type = response[2]
        if 'error_messages' in archive_response:
            error_messages = archive_response.get('error_messages')
            accession = '' #TODO
            return ERRORED_ENTITY, ArchiveResponse(entity_type, accession, error_messages)
        else:
            is_update = response[1]
            accession = archive_response.get('accession')
            if is_update:
                return UPDATED_ENTITY, ArchiveResponse(entity_type, accession)
            else:
                return CREATED_ENTITY, ArchiveResponse(entity_type, accession)

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
