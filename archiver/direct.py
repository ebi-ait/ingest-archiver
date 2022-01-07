import config
from archiver import first_element_or_self
from converter.ena.ena_study import EnaStudyConverter

from hca.loader import HcaLoader, IngestApi
from hca.submission import HcaSubmission
from hca.updater import HcaUpdater
from converter.biosamples import BioSamplesConverter
from submitter.base import CREATED_ENTITY
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

    def archive_project(self, project_uuid: str) -> HcaSubmission:
        hca_submission = self.__loader.get_project(project_uuid=project_uuid)
        self.__archive(hca_submission)
        return hca_submission

    def archive_submission(self, submission_uuid: str) -> HcaSubmission:
        hca_submission = self.__loader.get_submission(submission_uuid=submission_uuid)
        accessions = self.__archive(hca_submission)
        return accessions

    def __archive(self, submission: HcaSubmission):
        ingest_entities_to_update = []
        if self.__biosamples_submitter:
            biosample_accessions = self.__archive_samples_to_biosamples(ingest_entities_to_update, submission)

        if self.__biostudies_submitter:
            biostudies_accessions = self.__archive_project_to_biostudies(ingest_entities_to_update, submission)

        if self.__biosamples_submitter and self.__biostudies_submitter:
            if self.__check_accessions_existence(biosample_accessions, biostudies_accessions):
                self.__exchange_sample_and_project_accessions(submission, biosample_accessions, biostudies_accessions[0])

        if self.__ena_submitter:
            ena_accessions = self.__archive_ena_entities(ingest_entities_to_update, submission)

        for entity in ingest_entities_to_update:
            submission.add_accessions_to_attributes(entity)
            # TODO There is a bug here. We have to investigate this later when we set the response accession into ingest
            # self.__updater.update_entity(entity)

        accessions = self.__archive_accessions(biosample_accessions, biostudies_accessions, ena_accessions)

        return accessions

    @staticmethod
    def __archive_accessions(biosample_accessions, biostudies_accession, ena_accessions):
        return {
            'biosamples_accessions': biosample_accessions,
            'biostudies_accessions': biostudies_accession,
            'ena_accessions': ena_accessions
        }

    @staticmethod
    def __check_accessions_existence(biosample_accessions, biostudies_accession):
        return biosample_accessions is not None and len(biosample_accessions) > 0 and \
                biostudies_accession is not None

    def __archive_project_to_biostudies(self, ingest_entities_to_update, submission):
        biostudies_entities, accessions = self.__biostudies_submitter.send_all_projects(submission)
        ingest_entities_to_update.extend(biostudies_entities.get(CREATED_ENTITY, []))
        return accessions

    def __archive_samples_to_biosamples(self, ingest_entities_to_update, submission):
        biosamples_entities, accessions = self.__biosamples_submitter.send_all_samples(submission)
        ingest_entities_to_update.extend(biosamples_entities.get(CREATED_ENTITY, []))
        return accessions

    def __archive_ena_entities(self, ingest_entities_to_update, submission):
        ena_entities, ena_accessions = self.__ena_submitter.send_all_ena_entities(submission)
        ingest_entities_to_update.extend(ena_entities.get(CREATED_ENTITY, []))
        return ena_accessions

    def __exchange_sample_and_project_accessions(self, submission, biosample_accessions: list, biostudies_accession):
        biostudies_accession = first_element_or_self(biostudies_accession)
        self.__biostudies_submitter.update_submission_with_sample_accessions(biosample_accessions,
                                                                             biostudies_accession)
        self.__biosamples_submitter.update_samples_with_biostudies_accession(submission, biosample_accessions,
                                                                             biostudies_accession)

    @staticmethod
    def create_submitter_for_biosamples(aap_password, aap_url, aap_user, biosamples_domain, biosamples_url):
        aap_client = AapClient(aap_user, aap_password, aap_url)
        biosamples_client = BioSamples(aap_client, biosamples_url)
        biosamples_converter = BioSamplesConverter(biosamples_domain)
        biosamples_submitter_service = BioSamplesSubmitterService(biosamples_client)
        biosamples_submitter = BioSamplesSubmitter(biosamples_client, biosamples_converter,
                                                   biosamples_submitter_service)
        return biosamples_submitter

    @staticmethod
    def create_submitter_for_biostudies(biostudies_url, biostudies_username, biostudies_password):
        biostudies_converter = BioStudiesConverter()
        biostudies_client = DirectArchiver.__create_biostudies_client(biostudies_password, biostudies_url, biostudies_username)
        biostudies_submitter_service = BioStudiesSubmitterService(biostudies_client)
        biostudies_submitter = BioStudiesSubmitter(biostudies_client, biostudies_converter,
                                                   biostudies_submitter_service)
        return biostudies_submitter

    @staticmethod
    def __create_biostudies_client(biostudies_password, biostudies_url, biostudies_username):
        return BioStudies(biostudies_url, biostudies_username, biostudies_password)

    @staticmethod
    def create_submitter_for_ena(ena_api_url, ena_api_username, ena_webin_password):
        ena_client = Ena(ena_api_url, ena_api_username, ena_webin_password)
        ena_study_converter = EnaStudyConverter()
        return EnaSubmitter(ena_client, ena_study_converter)


def direct_archiver_from_params(
        ingest_url: str,
        biosamples_url: str, biosamples_domain: str, aap_url: str, aap_user: str, aap_password: str,
        biostudies_url: str, biostudies_username: str, biostudies_password: str,
        ena_api_url: str, ena_webin_username: str, ena_webin_password: str
) -> DirectArchiver:
    ingest_client = IngestApi(ingest_url)
    hca_loader = HcaLoader(ingest_client)
    hca_updater = HcaUpdater(ingest_client)

    biosamples_submitter = DirectArchiver.create_submitter_for_biosamples(aap_password, aap_url, aap_user,
                                                                          biosamples_domain, biosamples_url)

    biostudies_submitter = DirectArchiver.create_submitter_for_biostudies(biostudies_url, biostudies_username,
                                                                          biostudies_password)

    ena_submitter = DirectArchiver.create_submitter_for_ena(ena_api_url, ena_webin_username, ena_webin_password)

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
