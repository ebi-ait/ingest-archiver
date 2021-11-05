import config

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


class DirectArchiver:
    def __init__(self, loader: HcaLoader, updater: HcaUpdater,
                 biosamples_submitter: BioSamplesSubmitter = None,
                 biostudies_submitter: BioStudiesSubmitter = None):
        self.__loader = loader
        self.__updater = updater
        self.__biosamples_submitter = biosamples_submitter
        self.__biostudies_submitter = biostudies_submitter

    def archive_project(self, project_uuid: str) -> HcaSubmission:
        hca_submission = self.__loader.get_project(project_uuid=project_uuid)
        self.__archive(hca_submission)
        return hca_submission

    def archive_submission(self, submission_uuid: str) -> HcaSubmission:
        hca_submission = self.__loader.get_submission(submission_uuid=submission_uuid)
        self.__archive(hca_submission)
        return hca_submission

    def __archive(self, submission: HcaSubmission):
        ingest_entities_to_update = []
        if self.__biosamples_submitter:
            biosample_accessions = self.__archive_samples_to_biosamples(ingest_entities_to_update, submission)
        # TODO dcp-ingest-central/448 BST Test env is not exposed to outside of EBI VPN
        if self.__biostudies_submitter:
            biostudies_accessions = self.__archive_project_to_biostudies(ingest_entities_to_update, submission)

        if self.__biosamples_submitter and self.__biostudies_submitter:
            if self.__check_accessions_existence(biosample_accessions, biostudies_accessions):
                self.__exchange_sample_and_project_accessions(submission, biosample_accessions, biostudies_accessions[0])

        for entity in ingest_entities_to_update:
            submission.add_accessions_to_attributes(entity)
            self.__updater.update_entity(entity)

    @staticmethod
    def __check_accessions_existence(biosample_accessions, biostudies_accession):
        return biosample_accessions is not None and len(biosample_accessions) > 0 and \
                biostudies_accession is not None

    def __archive_project_to_biostudies(self, ingest_entities_to_update, submission):
        biostudies, accessions = self.__biostudies_submitter.send_all_projects(submission)
        ingest_entities_to_update.extend(biostudies.get(CREATED_ENTITY, []))
        return accessions

    def __archive_samples_to_biosamples(self, ingest_entities_to_update, submission):
        biosamples, accessions = self.__biosamples_submitter.send_all_samples(submission)
        ingest_entities_to_update.extend(biosamples.get(CREATED_ENTITY, []))
        return accessions

    def __exchange_sample_and_project_accessions(self, submission, biosample_accessions: list, biostudies_accession):
        self.__biostudies_submitter.update_submission_with_sample_accessions(biosample_accessions,
                                                                             biostudies_accession)
        self.__biosamples_submitter.update_samples_with_biostudies_accession(submission, biosample_accessions,
                                                                             biostudies_accession)
        # TODO add biostudies accession to samples in ebi-ait/dcp-ingest-central#497


def direct_archiver_from_params(
        ingest_url: str,
        biosamples_url: str, biosamples_domain: str, aap_url: str, aap_user: str, aap_password: str,
        biostudies_url: str, biostudies_username: str, biostudies_password: str
) -> DirectArchiver:
    ingest_client = IngestApi(ingest_url)
    hca_loader = HcaLoader(ingest_client)
    hca_updater = HcaUpdater(ingest_client)
    aap_client = AapClient(aap_user, aap_password, aap_url)

    biosamples_client = BioSamples(aap_client, biosamples_url)
    biosamples_converter = BioSamplesConverter(biosamples_domain)
    biosamples_submitter_service = BioSamplesSubmitterService(biosamples_client)
    biosamples_submitter = BioSamplesSubmitter(biosamples_client, biosamples_converter, biosamples_submitter_service)

    # TODO when we solved the issue with BioStudies availability, then we can remove the above condition
    if config.BIOSTUDIES_ENV == 'dev':
        biostudies_converter = BioStudiesConverter()
        biostudies_client = BioStudies(biostudies_url, biostudies_username, biostudies_password)
        biostudies_submitter_service = BioStudiesSubmitterService(biostudies_client)
        biostudies_submitter = BioStudiesSubmitter(biostudies_client, biostudies_converter, biostudies_submitter_service)
    else:
        biostudies_submitter = None

    return DirectArchiver(loader=hca_loader, updater=hca_updater,
                          biosamples_submitter=biosamples_submitter,
                          biostudies_submitter=biostudies_submitter)


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
        'biostudies_password': config.BIOSTUDIES_PASSWORD
    }
    return direct_archiver_from_params(**params)
