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
    'SUBMISSION': 'ENA submission'
}


class EnaSubmitter(Submitter):
    def __init__(self, archive_client: Ena, updater: HcaUpdater):
        super().__init__(archive_client, None, updater)
        self.__archive_client = archive_client

    def send_all_ena_entities(self, submission: HcaSubmission) -> dict:
        converted_entities = self.convert_all_entities(submission, ARCHIVE_TYPE)
        responses = self.send_all_entities(converted_entities, ARCHIVE_TYPE)
        self.process_responses(submission, responses, ERROR_KEY, ARCHIVE_TYPE)

        return responses[0]

    def _submit_to_archive(self, converted_entity):
        ena_files = {}
        entity_type = converted_entity.hca_entity_type
        if entity_type == 'projects':
            ena_files['STUDY'] = ('STUDY.xml', converted_entity.data)

        ena_action = EnaAction.ADD
        if converted_entity.updated:
            ena_action = EnaAction.MODIFY

        response = self.__archive_client.send_submission(
            ena_files, ena_action, self.release_date, 'HCA')

        response_xml = ElementTree.fromstring(response.decode('utf-8'))

        return self.__process_xml_response(response_xml)

    @staticmethod
    def __process_xml_response(response: Element):
        success = response.attrib.get('success')
        processed_response = {}
        if success == 'true':
            processed_response = EnaSubmitter.__gather_accession_and_uuid_from_response('STUDY', response)
        else:
            ena_types = ['STUDY', 'SUBMISSION']
            for ena_type in ena_types:
                processed_response.setdefault('error_message', {}).setdefault('ena', {})[ena_type] = \
                    EnaSubmitter.__get_failure_response_by_entity(response)

        return processed_response

    @staticmethod
    def __gather_accession_and_uuid_from_response(ena_type, response):
        accessions_by_uuid = []
        for entity in response.findall(ena_type):
            accessions_by_uuid.append(
                {
                    "accession": entity.attrib.get('accession'),
                    "uuid": entity.attrib.get('alias')
                }
            )

        return {
                "entity_type": HCA_TYPE_BY_ENA_TYPE.get(ena_type),
                "uuid": accessions_by_uuid[0].get("uuid"),
                "ena_project_accession": accessions_by_uuid[0].get('accession')
        }

    @staticmethod
    def __is_update_request(response):
        is_update = False
        for action in response.findall('ACTIONS'):
            if action.text in ['ADD', 'MODIFY']:
                is_update = action.text == 'MODIFY'
                break
        return is_update

    @staticmethod
    def __get_failure_response_by_entity(response):
        messages: list = EnaSubmitter.__get_messages_from_response(response)

        return messages

    @staticmethod
    def __get_messages_from_response(response) -> List:
        messages = []
        for message in response.find('MESSAGES'):
            error_message: str = message.text
            messages.append(f'{message.tag}: {error_message}')

        return messages
