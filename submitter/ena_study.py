from typing import List, Tuple
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from submission_broker.submission.submission import Submission

from converter.ena.ena_study import EnaStudyConverter
from submitter.base import Submitter
from submitter.ena import Ena, EnaAction

ERROR_KEY = 'content.project_core.ena_study_accession'


class EnaSubmitter(Submitter):
    def __init__(self, archive_client: Ena, converter: EnaStudyConverter):
        super().__init__(archive_client, converter)
        self.__archive_client = archive_client
        self.__converter = converter

    def send_all_ena_entities(self, submission: Submission) -> Tuple[dict, List[str]]:
        response, accessions = self.send_all_entities(submission, "ENA", ERROR_KEY)

        return response, accessions

    def _submit_to_archive(self, converted_entity):
        # hardcoded for now, but it is going to change when we add more types to this dict
        ena_files = {
            'STUDY': ('STUDY.xml', converted_entity)
        }

        response = self.__archive_client.send_submission(
            ena_files, EnaAction.ADD, self.release_date, 'HCA')

        response_xml = ElementTree.fromstring(response.decode('utf-8'))

        return {'accession': self.__get_accession(response_xml)}

    @staticmethod
    def __get_accession(response: Element):
        for ena_entity in response.iter('STUDY'):
            return ena_entity.attrib.get('accession')
