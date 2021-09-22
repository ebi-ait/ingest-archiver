import os
import xml
from unittest import TestCase
from unittest.mock import Mock, patch, mock_open

import xmltodict

from ena.ena_api import EnaApi
from ena.util import load_xml_dict, load_xml_tree_from_string, load_json


class EnaApiTest(TestCase):
    def setUp(self) -> None:
        self.ingest_api = Mock()
        self.ena_api = EnaApi(self.ingest_api)
        self.expected_dir = os.path.dirname(__file__) + '/data'

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

    def test_process_result(self):
        self.ingest_api.get_entity = Mock(return_value={'content': {}})
        self.ingest_api.patch = Mock()
        run_data = load_json(f'{self.expected_dir}/sequencing_run_data__with_ftp_dir.json')
        run_data2 = load_json(f'{self.expected_dir}/sequencing_run_data__with_ftp_dir_2.json')
        result = """<?xml version='1.0' encoding='UTF-8'?>
        <RECEIPT receiptDate="2021-08-05T11:27:47.033+01:00" submissionFile="submission.xml" success="true">
             <RUN accession="ERR6414234" alias="sequencingRun_21aa0e1a-a31b-42ae-a82b-5773c481e36b_1" status="PRIVATE" />
             <SUBMISSION accession="ERA5468875" alias="SUBMISSION-05-08-2021-11:27:46:832" />
             <MESSAGES>
                  <INFO>This submission is a TEST submission and will be discarded within 24 hours</INFO>
             </MESSAGES>
             <ACTIONS>ADD</ACTIONS>
        </RECEIPT>
        """

        report = self.ena_api.process_receipt(result, [run_data, run_data2])

        expected = {
            'not_updated': [
                {
                    'file_url': 'url1',
                    'alias': 'sequencingRun_21aa0e1a-a31b-42ae-a82b-5773c481e36c_1',
                    'error': 'no accession'
                },
                {
                    'file_url': 'url2',
                    'alias': 'sequencingRun_21aa0e1a-a31b-42ae-a82b-5773c481e36c_1',
                    'error': 'no accession'
                },
                {
                    'file_url': 'url3',
                    'alias': 'sequencingRun_21aa0e1a-a31b-42ae-a82b-5773c481e36c_1',
                    'error': 'no accession'
                }
            ],
            'updated': [
                {
                    'file_url': 'https://api.ingest.archive.data.humancellatlas.org/files/60f05d0ad5d575160aafb250',
                    'alias': 'sequencingRun_21aa0e1a-a31b-42ae-a82b-5773c481e36b_1',
                    'accession': 'ERR6414234'
                },
                {
                    'file_url': 'https://api.ingest.archive.data.humancellatlas.org/files/60f05d0ad5d575160aafb251',
                    'alias': 'sequencingRun_21aa0e1a-a31b-42ae-a82b-5773c481e36b_1',
                    'accession': 'ERR6414234'
                },
                {
                    'file_url': 'https://api.ingest.archive.data.humancellatlas.org/files/60f05d0ad5d575160aafb252',
                    'alias': 'sequencingRun_21aa0e1a-a31b-42ae-a82b-5773c481e36b_1',
                    'accession': 'ERR6414234'}
            ]
        }

        self.assertEqual(report, expected)
