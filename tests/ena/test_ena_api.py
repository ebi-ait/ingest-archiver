import xml
from unittest import TestCase
from unittest.mock import Mock, patch, mock_open

import xmltodict

from ena.ena_api import EnaApi
from ena.util import load_xml_dict, load_xml_tree_from_string


class EnaApiTest(TestCase):
    def setUp(self) -> None:
        self.ingest_api = Mock()
        self.ena_api = EnaApi(self.ingest_api)
        self.expected_dir = 'data'

    def test_create_submission_xml(self):
        submission_xml_path = self.ena_api.create_submission_xml()
        actual = load_xml_dict(submission_xml_path)
        expected = xmltodict.parse(f"""
        <SUBMISSION>
           <ACTIONS>
              <ACTION>
                 <ADD/>
              </ACTION>
           </ACTIONS>
        </SUBMISSION>
        """)

        self.assertEqual(actual, expected)

    def test_create_submission_xml__modify(self):
        submission_xml_path = self.ena_api.create_submission_xml('MODIFY')
        actual = load_xml_dict(submission_xml_path)
        expected = xmltodict.parse(f"""
        <SUBMISSION>
           <ACTIONS>
              <ACTION>
                 <MODIFY/>
              </ACTION>
           </ACTIONS>
        </SUBMISSION>
        """)

        self.assertEqual(actual, expected)

    def test_create_xml_files(self):
        self.ena_api.create_run_xml_from_manifests = Mock(return_value={'run_xml_path': 'run.xml', 'all_run_data': []})
        self.ena_api.create_submission_xml = Mock(return_value='submission.xml')

        output = self.ena_api.create_xml_files(['m1', 'm2'], 'md5.txt')
        self.assertEqual({'all_run_data': [],
                          'run_xml_path': 'run.xml',
                          'submission_xml_path': 'submission.xml'}, output)
