import os
import tempfile
import xml.etree.ElementTree as ET
from typing import List

import requests

from api.ingest import IngestAPI
from ena.sequencing_run_converter import SequencingRunConverter
from ena.util import write_xml

ENA_API_DEV = 'https://wwwdev.ebi.ac.uk/ena/submit/drop-box/submit/'
INGEST_API = 'https://api.ingest.staging.archive.data.humancellatlas.org/'


class EnaApi:
    def __init__(self, url=None):
        self.url = os.environ.get('ENA_API', ENA_API_DEV)
        self.user = os.environ.get('ENA_USER', ENA_API_DEV)
        self.password = os.environ.get('ENA_PASSWORD', ENA_API_DEV)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.xml_dir = self.temp_dir.name
        # TODO for now use current work dir
        self.xml_dir = os.getcwd()
        self.ingest_api = IngestAPI(url=INGEST_API)
        self.run_converter = SequencingRunConverter(self.ingest_api)

    def submit_run_xml(self, manifests_ids: List[str], no_dir: bool = False):
        for manifest_id in manifests_ids:
            run_data = self.run_converter.prepare_sequencing_run_data(manifest_id, no_dir)
            lane_index = run_data.get('lane_index', '0')
            run_xml_tree = self.run_converter.convert_sequencing_run_data_to_xml_tree(run_data)
            run_xml_path = f'{self.xml_dir}/run_{manifest_id}_{lane_index}.xml'
            write_xml(run_xml_tree, run_xml_path)

        submission_xml_file = self.create_submission_xml()

        result = self.submit(run_xml_path, submission_xml_file)
        return result

    def submit(self, run_xml_path, submission_xml_file):
        files = {
            'SUBMISSION': open(submission_xml_file, 'r'),
            'RUN': open(run_xml_path, 'r'),
        }
        r = requests.post(self.url, files=files, auth=(self.user, self.password))
        r.raise_for_status()
        result = r.json()
        return result

    def create_submission_xml(self):
        submission_xml_as_string = """
        <SUBMISSION>
           <ACTIONS>
              <ACTION>
                 <ADD/>
              </ACTION>
           </ACTIONS>
        </SUBMISSION>
        """

        submission = ET.fromstring(submission_xml_as_string)
        submission_xml_tree = ET.ElementTree(submission)

        path = f'{self.xml_dir}/submission.xml'
        write_xml(submission_xml_tree, path)
        return path
