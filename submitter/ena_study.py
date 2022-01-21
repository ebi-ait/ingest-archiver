from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from submission_broker.submission.submission import Submission

from converter.ena.ena_study import EnaStudyConverter
from hca.updater import HcaUpdater
from submitter.base import Submitter
from submitter.ena import Ena, EnaAction

ERROR_KEY = 'content.project_core.ena_study_accession'


class EnaSubmitter(Submitter):
    def __init__(self, archive_client: Ena, converter: EnaStudyConverter, updater: HcaUpdater):
        super().__init__(archive_client, converter, updater)
        self.__archive_client = archive_client
        self.__converter = converter

    def send_all_ena_entities(self, submission: Submission) -> dict:
        response = self.send_all_entities(submission, "ENA", ERROR_KEY)

        return response

    def _submit_to_archive(self, converted_entity: dict):
        # hardcoded for now, but it is going to change when we add more types to this dict
        ena_files = {
            'STUDY': ('STUDY.xml', converted_entity)
            # 'SAMPLE': ('SAMPLE.xml', converted_entity)
        }

        response = self.__archive_client.send_submission(
            ena_files, EnaAction.ADD, self.release_date, 'HCA')

        response_xml = ElementTree.fromstring(response.decode('utf-8'))

        return self.__process_response(response_xml)

    @staticmethod
    def __process_response(response: Element):
        success = response.attrib.get('success')
        if success == 'true':
            study = response.find('STUDY')
            return {
                'accession': study.attrib.get('accession')
            }
        else:
            messages = []
            for message in response.find('MESSAGES'):
                messages.append(f'{message.tag}: {message.text}')
            return {
                'error_messages': messages
            }