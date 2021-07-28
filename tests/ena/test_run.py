from unittest import TestCase

from ena.ena_api import EnaApi


class SampleRunTest(TestCase):
    def setUp(self) -> None:
        self.ena_api = EnaApi(url='https://api.ingest.staging.archive.data.humancellatlas.org/')

    def test_submit_run_xml(self):
        # self.ena_api.submit_run_xml(['60fffb7eb1f910182d1a84ff'], True)
        pass
