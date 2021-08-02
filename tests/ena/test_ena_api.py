from unittest import TestCase
from unittest.mock import Mock, patch, mock_open

from ena.ena_api import EnaApi
from ena.util import load_xml


class EnaApiTest(TestCase):
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

    def test_create_xml_files(self):
        path = {
            'm1': 'run_for_m1.xml',
            'm2': 'run_for_m2.xml'
        }
        data = {
            'submission.xml': 'submission_data',
            'run_for_m1.xml': 'm1_seq_run_data',
            'run_for_m2.xml': 'm2_seq_run_data'
        }

        self.ena_api.create_run_xml_from_manifest = lambda manifest, x, y: path.get(manifest)
        self.ena_api.create_submission_xml = Mock(return_value='submission.xml')

        with patch("builtins.open", mock_open(lambda p, _: data.get(p))):
            files = self.ena_api.create_xml_files(['m1', 'm2'], 'md5.txt')
            self.assertEqual(files,
                             [('SUBMISSION', 'submission_data'),
                              ('RUN', 'm1_seq_run_data'),
                              ('RUN', 'm2_seq_run_data')])
