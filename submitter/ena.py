from typing import Tuple, List
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from archiver import ArchiveResponse, ConvertedEntity
from hca.submission import HcaSubmission
from hca.updater import HcaUpdater
from submitter.base import Submitter
from submitter.ena_submitter_service import Ena, EnaAction

ARCHIVE_TYPE = "ENA"

ERROR_KEY = 'content.project_core.ena_study_accession'

HCA_TYPE_BY_ENA_TYPE = {
    'STUDY': 'projects',
    'SAMPLE': 'biomaterials'
}


class EnaSubmitter(Submitter):
    def __init__(self, archive_client: Ena, updater: HcaUpdater):
        super().__init__(archive_client, None, updater)
        self.__archive_client = archive_client

    def send_all_ena_entities(self, submission: HcaSubmission) -> dict:
        converted_entities = self.convert_all_entities(submission, ARCHIVE_TYPE)
        responses = self.send_all_entities(converted_entities, ARCHIVE_TYPE)
        processed_responses = self.process_responses(submission, responses, ERROR_KEY, ARCHIVE_TYPE)

        return processed_responses

    def _submit_to_archive(self, converted_entities: List[ConvertedEntity]):
        ena_files = {}
        for converted_entity in converted_entities:
            entity_type = converted_entity.hca_entity_type
            if entity_type == 'projects':
                ena_files['STUDY'] = ('STUDY.xml', converted_entity.data)
            elif entity_type == 'biomaterials':
                ena_files['SAMPLE'] = ('SAMPLE.xml', converted_entity.data)

            if converted_entity.is_update:
                ena_action = EnaAction.MODIFY
            else:
                ena_action = EnaAction.ADD

        response = self.__archive_client.send_submission(
            ena_files, ena_action, self.release_date, 'HCA')

        response_xml = ElementTree.fromstring(response.decode('utf-8'))

        return self.__process_response(response_xml)

    @staticmethod
    def __process_response(response: Element):
        success = response.attrib.get('success')
        ena_types = ['SUBMISSION', 'STUDY', 'SAMPLE']
        processed_response = []
        if success == 'true':
            is_update = EnaSubmitter.__is_update_request(response)
            for ena_type in ena_types:
                EnaSubmitter.__gather_accession_and_uuid_from_response(ena_type, is_update, processed_response,
                                                                       response)
        else:
            for ena_type in ena_types:
                EnaSubmitter.__get_failure_response_by_entity(ena_type, processed_response, response)

        return processed_response

    @staticmethod
    def __gather_accession_and_uuid_from_response(ena_type, is_update, processed_response, response):
        for entity in response.findall(ena_type):
            data = {"accession": entity.attrib.get('accession'), 'uuid': entity.attrib.get('alias')}
            entity_type = HCA_TYPE_BY_ENA_TYPE.get(ena_type, '')
            processed_response.append(
                ArchiveResponse(entity_type=entity_type, data=data, is_update=is_update)
            )

    @staticmethod
    def __is_update_request(response):
        is_update = False
        for action in response.findall('ACTIONS'):
            if action.text in ['ADD', 'MODIFY']:
                is_update = action.text == 'MODIFY'
                break
        return is_update

    @staticmethod
    def __get_failure_response_by_entity(ena_type, processed_response, response):
        for entity in response.findall(ena_type):
            ena_entity_uuid: str = entity.attrib.get('alias')
            messages: list = EnaSubmitter.__get_messages_from_response(ena_entity_uuid, response)
            data = {'uuid': ena_entity_uuid}
            entity_type = HCA_TYPE_BY_ENA_TYPE.get(ena_type, '')
            processed_response.append(
                ArchiveResponse(entity_type=entity_type, data=data, error_messages=messages, is_update=False)
            )

    @staticmethod
    def __get_messages_from_response(ena_entity_uuid, response) -> List:
        messages = []
        for message in response.find('MESSAGES'):
            error_message: str = message.text
            messages.append(f'{message.tag}: {error_message}')

        return messages
