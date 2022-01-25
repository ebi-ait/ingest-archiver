from typing import Tuple
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from converter.ena.ena_study import EnaStudyConverter
from hca.submission import HcaSubmission
from hca.updater import HcaUpdater
from submitter.base import Submitter
from submitter.ena import Ena, EnaAction

ARCHIVE_TYPE = "ENA"

ERROR_KEY = 'content.project_core.ena_study_accession'


class EnaSubmitter(Submitter):
    def __init__(self, archive_client: Ena, converter: EnaStudyConverter, updater: HcaUpdater):
        super().__init__(archive_client, converter, updater)
        self.__archive_client = archive_client
        self.__converter = converter

    def send_all_ena_entities(self, submission: HcaSubmission) -> dict:
        converted_entities = self.convert_all_entities(submission, ARCHIVE_TYPE)
        responses = self.send_all_entities(converted_entities, ARCHIVE_TYPE)
        processed_responses = self.process_responses(submission, responses, ERROR_KEY)

        return processed_responses

    def _submit_to_archive(self, converted_entities: Tuple[dict, bool, str]):
        ena_files = {}
        for converted_entity, is_update, entity_type in converted_entities:
            if entity_type == 'projects':
                ena_files['STUDY'] = ('STUDY.xml', converted_entity)
            elif entity_type == 'biomaterials':
                ena_files['SAMPLE'] = ('SAMPLE.xml', converted_entity)

            if is_update:
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
        processed_response = []
        if success == 'true':
            ena_types = ['STUDY', 'SAMPLE']
            is_update = False
            for action in response.findall('ACTIONS'):
                if action.text in ['ADD', 'MODIFY']:
                    is_update = action.text == 'MODIFY'
                    break
            for ena_type in ena_types:
                for entity in response.findall(ena_type):
                    processed_response.append(
                        ({"accession": entity.attrib.get('accession')}, is_update, ena_type.lower())
                    )
        else:
            messages = []
            for message in response.find('MESSAGES'):
                messages.append(f'{message.tag}: {message.text}')
            processed_response.append(
                ({'error_messages': messages}, False, 'study')
            )

        return processed_response
