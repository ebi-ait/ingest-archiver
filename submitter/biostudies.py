from typing import List

from submission_broker.services.biostudies import BioStudies
from submission_broker.submission.submission import Submission, Entity

from converter.biostudies import BioStudiesConverter
from submitter.base import Submitter

ERROR_KEY = 'content.project_core.biostudies_accession'

BIOSAMPLE_LINK_TYPE = 'biosample'


class BioStudiesSubmitter(Submitter):
    def __init__(self, archive_client: BioStudies, converter: BioStudiesConverter):
        super().__init__(archive_client, converter)
        self.__archive_client = archive_client
        self.__converter = converter

    def send_all_projects(self, submission: Submission) -> dict:
        response, accessions = self.send_all_entities(submission, "BioStudies", ERROR_KEY)

        return response, accessions

    def _submit_to_archive(self, converted_entity):
        response = {'accession': self.__archive_client.send_submission(converted_entity)}

        return response

    def update_submission_with_sample_accessions(self, biosample_accessions: list, biostudies_accession):
        biostudies_submission = self.get_biostudies_payload_by_accession(biostudies_accession).json
        links_section = self.__get_links_section_from_submission(biostudies_submission)
        self.__update_links_section(links_section, biosample_accessions)
        self.__archive_client.send_submission(biostudies_submission)

        return biostudies_submission

    def get_biostudies_payload_by_accession(self, accession):
        return self.__archive_client.get_submission_by_accession(accession)

    @staticmethod
    def __get_links_section_from_submission(submission: dict) -> List:
        section = submission.get('section')
        return section.setdefault('links', [])

    def __update_links_section(self, links_section, biosample_accessions):
        for biosample_accession in biosample_accessions:
            link_to_add = self.__create_link_element(BIOSAMPLE_LINK_TYPE, biosample_accession)
            links_section.append(link_to_add)

    @staticmethod
    def __create_link_element(link_type, accession):
        return {
            'url': accession,
            'attributes': [
                {
                    'name': 'Type',
                    'value': link_type
                }
            ]
        }