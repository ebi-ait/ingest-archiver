from typing import List

from submission_broker.services.biostudies import BioStudies


class BioStudiesSubmitterService:

    BIOSAMPLE_LINK_TYPE = 'biosample'
    ENA_LINK_TYPE = 'ena'

    def __init__(self, archive_client: BioStudies):
        self.__archive_client = archive_client

    def update_submission_with_accessions_by_type(self, biostudies_submission,
                                                  accessions: List[str], link_type: str):
        links_section = self.__get_links_section_from_submission(biostudies_submission)
        self.__update_links_section(links_section, accessions, link_type)

    def get_biostudies_payload_by_accession(self, accession):
        return self.__archive_client.get_submission_by_accession(accession)

    @staticmethod
    def __get_links_section_from_submission(submission: dict) -> List:
        section = submission.get('section', {})
        return section.setdefault('links', [])

    def __update_links_section(self, links_section, accessions: List[str], link_type: str):
        for accession in accessions:
            if accession:
                link_to_add = self.__create_link_element(link_type, accession)
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