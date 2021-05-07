import config
from hca.loader import HcaLoader, IngestApi
from hca.submission import HcaSubmission
from hca.updater import HcaUpdater
from converter.biosamples import BioSamplesConverter
from submitter.biosamples import BioSamplesSubmitter
from submission_broker.services.biosamples import BioSamples, AapClient


class DirectArchiver:
    def __init__(self, loader: HcaLoader, updater: HcaUpdater, biosamples_submitter: BioSamplesSubmitter = None):
        self.__loader = loader
        self.__updater = updater
        self.__biosamples_submitter = biosamples_submitter
        self.__biostudies_submitter = None

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
            biosamples = self.__biosamples_submitter.send_all_samples(submission)
            ingest_entities_to_update.extend(biosamples.get('CREATED', []))
        if self.__biostudies_submitter:
            raise NotImplementedError("BioStudies Submitter not implemented")
        for entity in ingest_entities_to_update:
            submission.add_accessions_to_attributes(entity)
            self.__updater.update_entity(entity)


def direct_archiver_from_params(
        ingest_url: str,
        biosamples_url: str, biosamples_domain: str, aap_url: str, aap_user: str, aap_password: str
) -> DirectArchiver:
    ingest_client = IngestApi(ingest_url)
    hca_loader = HcaLoader(ingest_client)
    hca_updater = HcaUpdater(ingest_client)
    aap_client = AapClient(aap_user, aap_password, aap_url)
    biosamples_client = BioSamples(aap_client, biosamples_url)
    biosamples_converter = BioSamplesConverter(biosamples_domain)
    submitter = BioSamplesSubmitter(biosamples_client, biosamples_converter)
    return DirectArchiver(loader=hca_loader, updater=hca_updater, biosamples_submitter=submitter)


def direct_archiver_from_config() -> DirectArchiver:
    params = {
        'ingest_url': config.INGEST_API_URL.strip('/'),
        'aap_url': config.AAP_API_URL.replace('/auth', ''),
        'aap_user': config.AAP_API_USER,
        'aap_password': config.AAP_API_PASSWORD,
        'biosamples_url': config.BIOSAMPLES_URL,
        'biosamples_domain': config.AAP_API_DOMAIN
    }
    return direct_archiver_from_params(**params)
