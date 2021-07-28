from unittest import TestCase
from unittest.mock import Mock, patch

from ena.ena_api import EnaApi
from ena.util import load_xml


class EnaApiTest(TestCase):

    # @patch('ena.ena_api.os')
    # def setUp(self, mock_os) -> None:
    def setUp(self) -> None:
        self.ingest_api = Mock()
        self.ena_api = EnaApi(self.ingest_api)
        self.expected_dir = 'data'

    def test_create_submission_xml(self):
        submission_xml_path = self.ena_api.create_submission_xml()
        actual = load_xml(submission_xml_path)

        expected_file = f'{self.expected_dir}/submission.xml'
        expected = load_xml(expected_file)

        self.assertEqual(actual, expected)

    # TODO
    def test_create_xml_files(self):
        pass

    # TODO
    def test_create_run_xml_from_manifest(self):
        pass

    # TODO
    def test_post_files(self):
        pass
