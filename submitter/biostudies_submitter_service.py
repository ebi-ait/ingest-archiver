from typing import List

from submission_broker.services.biostudies import BioStudies

BIOSAMPLE_LINK_TYPE = 'biosample'


class BioStudiesSubmitterService:

    def __init__(self, archive_client: BioStudies):
        self.__archive_client = archive_client

    def update_submission_with_sample_accessions(self, biosample_accessions: list, biostudies_accession):
        if biosample_accessions is None or len(biosample_accessions) <= 0:
            return None

        biostudies_submission = self.__get_biostudies_payload_by_accession(biostudies_accession).json
        links_section = self.__get_links_section_from_submission(biostudies_submission)
        self.__update_links_section(links_section, biosample_accessions)

        return biostudies_submission

    def __get_biostudies_payload_by_accession(self, accession):
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