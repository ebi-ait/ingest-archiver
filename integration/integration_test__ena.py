import os

from api.ingest import IngestAPI
from ena.ena_api import EnaApi
from unittest import TestCase

ENA_API_DEV = 'https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/'
INGEST_ARCHIVER_API_STAGING = "https://archiver.ingest.staging.archive.data.humancellatlas.org"
INGEST_API = 'https://api.ingest.staging.archive.data.humancellatlas.org/'


# TODO This integration test is WIP


class SampleRunTest(TestCase):
    def setUp(self) -> None:
        self.ingest_api = IngestAPI(url=INGEST_API)
        self.ena_api = EnaApi(self.ingest_api, url=ENA_API_DEV)

    def test_submit_run_xml(self):
        # TODO
        # 1. Create submission in Ingest by uploading the 10x.xlsx spreadsheet
        # 2. Sync the 10x fastq files from hca-util upload area ab4f37be-7fd3-4c8f-9f12-7cfb55ef7131 to the submission upload area
        # 3. Submit the submission for archiving to DSP. Only submit project, study, samples, and sequencing experiment.
        # 4. Verify that the assay process has been updated with the correct sequencing experiment accession from step 3.
        ingest_submission_uuid = ''  # Replace this with submission uuid from step 1.
        manifest_ids = self.ingest_api.get_manifest_ids_from_submission(ingest_submission_uuid)
        # 5. Files need to be ftp-ed to the ftp upload area
        # 6. MD5 Checksum the files
        dir = os.path.dirname(os.path.realpath(__file__))
        md5_file = f'{dir}/md5.txt'
        self.ena_api.submit_run_xml_files(manifest_ids, md5_file)
        # 7. Assert that the files have the run accessions