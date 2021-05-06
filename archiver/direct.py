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
        self.archive(hca_submission)
        return hca_submission

    def archive_submission(self, submission_uuid: str) -> HcaSubmission:
        hca_submission = self.__loader.get_submission(submission_uuid=submission_uuid)
        self.archive(hca_submission)
        return hca_submission

    def archive(self, submission: HcaSubmission):
        ingest_entities_to_update = []
        if self.__biosamples_submitter:
            biosamples = self.__biosamples_submitter.send_all_samples(submission)
            ingest_entities_to_update.extend(biosamples.get('CREATED', []))
        if self.__biostudies_submitter:
            raise NotImplementedError("BioStudies Submitter not implemented")
        for entity in ingest_entities_to_update:
            submission.add_accessions_to_attributes(entity)
            self.__updater.update_entity(entity)


def direct_archiver_from_config() -> DirectArchiver:
    ingest = IngestApi(config.INGEST_API_URL.strip('/'))
    aap = AapClient(config.AAP_API_USER, config.AAP_API_PASSWORD, config.AAP_API_URL.replace('/auth', ''))
    biosamples = BioSamples(aap, config.BIOSAMPLES_URL)
    biosamples_converter = BioSamplesConverter(config.AAP_API_DOMAIN)
    return DirectArchiver(
        loader=HcaLoader(ingest),
        updater=HcaUpdater(ingest),
        biosamples_submitter=BioSamplesSubmitter(biosamples, biosamples_converter)
    )

