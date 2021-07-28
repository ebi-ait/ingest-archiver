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

    def test_submit_run_xml(self):
        manifest_ids = self.ingest_api.get_manifest_ids_from_submission(self.ingest_submission_uuid)
        dir = os.path.dirname(os.path.realpath(__file__))
        md5_file = f'{dir}/md5.txt'
        files = self.ena_api.create_xml_files(manifest_ids, md5_file, True)
        result_xml_tree = self.ena_api.post_files(files)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        write_xml(result_xml_tree, f'receipt_{timestamp}.xml')
