import os
import time

import polling
import requests

from api.ingest import IngestAPI
from ena.ena_api import EnaApi
from unittest import TestCase

from ena.util import write_json, write_xml

ENA_API_DEV = 'https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/'
INGEST_ARCHIVER_API_STAGING = "https://archiver.ingest.staging.archive.data.humancellatlas.org"
INGEST_API = 'https://api.ingest.staging.archive.data.humancellatlas.org/'

TIMEOUT = 60
STEP = 5


class SampleRunTest(TestCase):
    def setUp(self) -> None:
        self.ingest_api = IngestAPI(url=INGEST_API)
        self.ena_api = EnaApi(self.ingest_api, url=ENA_API_DEV)
        self.ingest_archiver_api_url = os.environ.get('INGEST_ARCHIVER_API_URL', INGEST_ARCHIVER_API_STAGING)
        self.ingest_archiver_api_key = os.environ.get('INGEST_ARCHIVER_API_KEY')
        self.headers = {
            'Api-Key': self.ingest_archiver_api_key
        }

        self.ingest_submission_uuid = '6fbcce27-f1ee-4606-a0b4-319f1d13b118'
        if not self.ingest_archiver_api_key:
            raise Exception(f'This test needs the api key to {self.ingest_archiver_api_url}')

    # def test_setup(self):
    #     ingest_submission_uuid = self._prepare_submission()
    #     self._archive_submission(ingest_submission_uuid)
    #
    #     archive_submission = polling.poll(
    #         lambda: self._get_latest_dsp_submission(ingest_submission_uuid),
    #         step=5,
    #         timeout=TIMEOUT
    #     )
    #
    #     self.dsp_submission_uuid = archive_submission['dspUuid']
    #
    #     valid = polling.poll(
    #         lambda: self._is_valid_dsp_submission(self.dsp_submission_uuid),
    #         step=5,
    #         timeout=TIMEOUT
    #     )
    #
    #     self._complete_submission(self.dsp_submission_uuid)

    # should run after test_setup
    def test_submit_run_xml(self):
        manifest_ids = self.ingest_api.get_manifest_ids_from_submission(self.ingest_submission_uuid)
        dir = os.path.dirname(os.path.realpath(__file__))
        md5_file = f'{dir}/md5.txt'
        files = self.ena_api.create_xml_files(manifest_ids, md5_file, True)
        result_xml_tree = self.ena_api.post_files(files)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        write_xml(result_xml_tree, f'receipt_{timestamp}.xml')


    def _prepare_submission(self):
        # TODO creation of submission
        # upload 10x spreadsheet
        # find small 10x fastq files
        # check ingest-integration-test repo on the automated test for archiving for guidance
        # see DatasetRunner.archived_run
        return self.ingest_submission_uuid

    def _archive_submission(self, ingest_submission_uuid: str):
        timestamp = time.strftime("%Y%m%d-%H%M%S")

        data = {
            'submission_uuid': ingest_submission_uuid,
            'alias_prefix': f'INGEST_INTEGRATION_TEST_{timestamp}',
            'exclude_types': 'sequencingRun'
        }

        archive_submission_url = f'{self.ingest_archiver_api_url}/archiveSubmissions'

        r = requests.post(archive_submission_url, json=data, headers=self.headers)
        r.raise_for_status()

    def _get_dsp_submission_uuid(self, ingest_submission_uuid):
        archive_submission = self._get_latest_dsp_submission(ingest_submission_uuid)
        return archive_submission['dspUuid'] if archive_submission else None

    def _get_latest_dsp_submission(self, ingest_submission_uuid):
        find_latest_url = f'{self.ingest_archiver_api_url}/latestArchiveSubmission/{ingest_submission_uuid}'
        r = requests.get(find_latest_url, headers=self.headers)

        if r.status_code == requests.codes.not_found:
            return None

        archive_submission = r.json()
        return archive_submission if archive_submission else None

    def _is_valid_dsp_submission(self, dsp_submission_uuid):
        result = self._get_validation_errors(dsp_submission_uuid)
        errors = result.get('errors')
        pending = result.get('pending')
        return (len(errors) == 0) and (len(pending) == 0)

    def _get_validation_errors(self, dsp_submission_uuid):
        get_validation_errors_url = f'{self.ingest_archiver_api_url}/archiveSubmissions/{dsp_submission_uuid}/validationErrors'
        r = requests.get(get_validation_errors_url, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def _complete_submission(self, dsp_submission_uuid):
        complete_url = f'{self.ingest_archiver_api_url}/archiveSubmissions/{dsp_submission_uuid}/complete'
        r = requests.post(complete_url, headers=self.headers)
        r.raise_for_status()
