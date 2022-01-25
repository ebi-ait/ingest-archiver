import logging

from biostudiesclient.exceptions import RestErrorException

import config
from archiver import first_element_or_self
from converter.ena.ena_study import EnaStudyConverter

from hca.loader import HcaLoader, IngestApi
from hca.submission import HcaSubmission
from hca.updater import HcaUpdater
from converter.biosamples import BioSamplesConverter
from submitter.biosamples import BioSamplesSubmitter
from submission_broker.services.biosamples import BioSamples, AapClient
from submission_broker.services.biostudies import BioStudies

from submitter.biosamples_submitter_service import BioSamplesSubmitterService
from submitter.biostudies import BioStudiesSubmitter
from converter.biostudies import BioStudiesConverter
from submitter.biostudies_submitter_service import BioStudiesSubmitterService
from submitter.ena import Ena
from submitter.ena_study import EnaSubmitter


class DirectArchiver:
    def __init__(self, loader: HcaLoader, updater: HcaUpdater, biosamples_submitter: BioSamplesSubmitter = None,
                 biostudies_submitter: BioStudiesSubmitter = None, ena_submitter: EnaSubmitter = None):
        self.__loader = loader
        self.__updater = updater
        self.__biosamples_submitter = biosamples_submitter
        self.__biostudies_submitter = biostudies_submitter
        self.__ena_submitter = ena_submitter
        self.logger = logging.getLogger(__name__)

    def archive_project(self, project_uuid: str) -> HcaSubmission:
        hca_submission = self.__loader.get_project(project_uuid=project_uuid)
        self.__archive(hca_submission)
        return hca_submission

    def archive_submission(self, submission_uuid: str) -> dict:
        hca_submission = self.__loader.get_submission(submission_uuid=submission_uuid)
        archives_response = self.__archive(hca_submission)
        return archives_response

    def __archive(self, submission: HcaSubmission):
        archives_responses = {}
        if self.__biosamples_submitter:
            biosamples_responses = self.__archive_samples_to_biosamples(submission)
            archives_responses['biosamples'] = biosamples_responses

        # if self.__biostudies_submitter:
        #     biostudies_responses = self.__archive_project_to_biostudies(submission)
        #     archives_responses['biostudies'] = biostudies_responses

        # TODO fix this with the refactored code
        # if self.__biosamples_submitter and self.__biostudies_submitter:
        #     if self.__check_accessions_existence(biosamples_responses, biostudies_accessions):
        #         self.__exchange_sample_and_project_accessions(submission, biosamples_responses, biostudies_accessions[0])

        if self.__ena_submitter:
            ena_responses = self.__archive_ena_entities(submission)
            archives_responses['ena'] = ena_responses

        return archives_responses

    @staticmethod
    def __archive_accessions(biosample_accessions, biostudies_accession, ena_accessions):
        return {
            'biosamples_accessions': biosample_accessions,
            'biostudies_accession': first_element_or_self(biostudies_accession),
            'ena_accessions': ena_accessions
        }

    @staticmethod
    def __check_accessions_existence(biosample_accessions, biostudies_accession):
        return biosample_accessions is not None and len(biosample_accessions) > 0 and \
                biostudies_accession is not None

    def __archive_project_to_biostudies(self, submission):
        biostudies_responses = self.__biostudies_submitter.send_all_projects(submission)
        self.__jsonify_archive_response(biostudies_responses)
        return biostudies_responses

    def __archive_samples_to_biosamples(self, submission):
        biosamples_responses = self.__biosamples_submitter.send_all_samples(submission)
        self.__jsonify_archive_response(biosamples_responses)
        return biosamples_responses

    def __archive_ena_entities(self, submission):
        ena_responses = self.__ena_submitter.send_all_ena_entities(submission)
        self.__jsonify_archive_response(ena_responses)
        return ena_responses

    @staticmethod
    def __jsonify_archive_response(archive_responses):
        for response_type, items in archive_responses.items():
            for index, response in enumerate(items):
                items[index] = response.__dict__

    def __exchange_sample_and_project_accessions(self, submission, biosample_accessions: list, biostudies_accession):
        biostudies_accession = first_element_or_self(biostudies_accession)
        self.__biostudies_submitter.update_submission_with_sample_accessions(biosample_accessions,
                                                                             biostudies_accession)
        self.__biosamples_submitter.update_samples_with_biostudies_accession(submission, biosample_accessions,
                                                                             biostudies_accession)

    @staticmethod
    def create_submitter_for_biosamples(aap_password, aap_url, aap_user, biosamples_domain, biosamples_url, hca_updater):
        aap_client = AapClient(aap_user, aap_password, aap_url)
        biosamples_client = BioSamples(aap_client, biosamples_url)
        biosamples_converter = BioSamplesConverter(biosamples_domain)
        biosamples_submitter_service = BioSamplesSubmitterService(biosamples_client)
        biosamples_submitter = BioSamplesSubmitter(biosamples_client, biosamples_converter,
                                                   biosamples_submitter_service, hca_updater)
        return biosamples_submitter

    @staticmethod
    def create_submitter_for_biostudies(biostudies_url, biostudies_username, biostudies_password, hca_updater):
        biostudies_converter = BioStudiesConverter()
        biostudies_client = DirectArchiver.__create_biostudies_client(biostudies_password, biostudies_url, biostudies_username)
        biostudies_submitter_service = BioStudiesSubmitterService(biostudies_client)
        biostudies_submitter = BioStudiesSubmitter(biostudies_client, biostudies_converter,
                                                   biostudies_submitter_service, hca_updater)
        return biostudies_submitter

    @staticmethod
    def __create_biostudies_client(biostudies_password, biostudies_url, biostudies_username):
        return BioStudies(biostudies_url, biostudies_username, biostudies_password)

    @staticmethod
    def create_submitter_for_ena(ena_api_url, ena_api_username, ena_webin_password, hca_updater):
        ena_client = Ena(ena_api_url, ena_api_username, ena_webin_password)
        ena_study_converter = EnaStudyConverter()
        return EnaSubmitter(ena_client, ena_study_converter, hca_updater)


def direct_archiver_from_params(
        ingest_url: str,
        biosamples_url: str, biosamples_domain: str, aap_url: str, aap_user: str, aap_password: str,
        biostudies_url: str, biostudies_username: str, biostudies_password: str,
        ena_api_url: str, ena_webin_username: str, ena_webin_password: str
) -> DirectArchiver:
    logger = logging.getLogger(__name__)
    ingest_client = IngestApi(ingest_url)
    hca_loader = HcaLoader(ingest_client)
    hca_updater = HcaUpdater(ingest_client)

    biosamples_submitter = \
        DirectArchiver.create_submitter_for_biosamples(aap_password, aap_url, aap_user, biosamples_domain,
                                                       biosamples_url, hca_updater)
    try:
        biostudies_submitter = DirectArchiver.create_submitter_for_biostudies(biostudies_url, biostudies_username,
                                                                              biostudies_password, hca_updater)
    except RestErrorException as rest_error:
        logger.error(f'Something went wrong with BioStudies service. Status code: {rest_error.status_code}, message: {rest_error.message}')
        biostudies_submitter = None
        # raise ArchiveException(rest_error.message, rest_error.status_code, 'BioStudies archive')

    ena_submitter = \
        DirectArchiver.create_submitter_for_ena(ena_api_url, ena_webin_username, ena_webin_password, hca_updater)

    return DirectArchiver(loader=hca_loader, updater=hca_updater,
                          biosamples_submitter=biosamples_submitter,
                          biostudies_submitter=biostudies_submitter,
                          ena_submitter=ena_submitter)


def direct_archiver_from_config() -> DirectArchiver:
    params = {
        'ingest_url': config.INGEST_API_URL.strip('/'),
        'aap_url': config.AAP_API_URL.replace('/auth', ''),
        'aap_user': config.AAP_API_USER,
        'aap_password': config.AAP_API_PASSWORD,
        'biosamples_url': config.BIOSAMPLES_URL,
        'biosamples_domain': config.AAP_API_DOMAIN,
        'biostudies_url': config.BIOSTUDIES_URL,
        'biostudies_username': config.BIOSTUDIES_USERNAME,
        'biostudies_password': config.BIOSTUDIES_PASSWORD,
        'ena_api_url': config.ENA_WEBIN_API_URL,
        'ena_webin_username': config.ENA_WEBIN_USERNAME,
        'ena_webin_password': config.ENA_WEBIN_PASSWORD
    }
    return direct_archiver_from_params(**params)
