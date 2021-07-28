import os
import tempfile
import xml
import xml.etree.ElementTree as ET
from typing import List

import requests

from api.ingest import IngestAPI
from ena.sequencing_run_converter import SequencingRunConverter
from ena.util import write_xml, load_xml_from_string


class EnaApi:
    def __init__(self, ingest_api: IngestAPI, url: str = None):
        self.url = url or os.environ.get('ENA_API_URL')
        self.user = os.environ.get('ENA_USER')
        self.password = os.environ.get('ENA_PASSWORD')

        self.temp_dir = tempfile.TemporaryDirectory()
        self.xml_dir = self.temp_dir.name
        # # TODO for testing locally
        # self.xml_dir = '_local'
        self.ingest_api = ingest_api
        self.run_converter = SequencingRunConverter(self.ingest_api)

    def _require_env_vars(self):
        if not self.url:
            raise Error('The ENA_API_URL be set in environment variables.')
        if not all([self.user, self.password]):
            raise Error('The ENA_USER, ENA_PASSWORD must be set in environment variables.')

    def submit_run_xml_files(self, manifests_ids: List[str], md5_file: str, in_root_dir: bool = False):
        files = self.create_xml_files(manifests_ids, md5_file, in_root_dir)
        result = self.post_files(files)
        return result

    def create_xml_files(self, manifests_ids, md5_file, in_root_dir):
        submission_xml_file = self.create_submission_xml()
        files = [('SUBMISSION', open(submission_xml_file, 'r'))]

        for manifest_id in manifests_ids:
            run_xml_path = self.create_run_xml_from_manifest(in_root_dir, manifest_id, md5_file)
            files.append(('RUN', open(run_xml_path, 'r')))

        return files

    def create_run_xml_from_manifest(self, in_root_dir, manifest_id, md5_file):
        run_data = self.run_converter.prepare_sequencing_run_data(manifest_id, md5_file, in_root_dir)
        run_xml_tree = self.run_converter.convert_sequencing_run_data_to_xml_tree(run_data)
        lane_index = run_data.get('lane_index', '0')
        run_xml_path = f'{self.xml_dir}/run_{manifest_id}_{lane_index}.xml'
        try:
            write_xml(run_xml_tree, run_xml_path)
        except Exception as e:
            print(e)
        return run_xml_path

    def post_files(self, files: dict):
        self._require_env_vars()
        r = requests.post(self.url, files=files, auth=(self.user, self.password))
        r.raise_for_status()
        result = load_xml_from_string(r.text)
        result_xml_tree = ET.ElementTree(result)
        return result_xml_tree

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


class Error(Exception):
    """Base-class for all exceptions raised by this module."""
