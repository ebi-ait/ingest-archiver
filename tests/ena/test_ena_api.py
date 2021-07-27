from unittest import TestCase

from ena.ena_api import EnaApi
from ena.util import write_xml, load_xml


class EnaApiTest(TestCase):
    def setUp(self) -> None:
        self.ena_api = EnaApi()

    def test_create_submission_xml(self):
        submission_xml_path = self.ena_api.create_submission_xml()
        actual = load_xml(submission_xml_path)

        expected_file = 'submission.xml'
        expected = load_xml(expected_file)

        self.assertEqual(actual, expected)

    def test_submit_run_xml(self):
        pass